import os
import sys
import re
import hashlib
import fnmatch
import chardet
import clang.cindex
from functools import lru_cache
from peewee import *

# LIBCLANG_PATH = "/usr/local/opt/llvm/lib/libclang.dylib" # Mac OS
LIBCLANG_PATH = "/usr/lib/llvm-6.0/lib/libclang.so"
clang.cindex.Config.set_library_file(LIBCLANG_PATH)

###################################
# Databse
###################################

database = SqliteDatabase(None, pragmas=(
    ('journal_mode', 'MEMORY'),
    ('synchronous',  'OFF')
))

class BaseModel(Model):
    class Meta:
        database = database

class FileHash(BaseModel):
    path = CharField(index=True, unique=True)
    hash = CharField()

class Definition(BaseModel):
    path = CharField(index=True)
    name = CharField(index=True, null=True)
    kind = CharField(null=True)
    type = CharField(null=True)
    line = IntegerField(null=True)

class Bookmark(BaseModel):
    path = CharField()
    alias = CharField(null=True)
    line = IntegerField(null=True)

class Memo(BaseModel):
    path = CharField()
    content = CharField()

def init_database(root, reset=False):
    if database.database:
        raise Exception("Database is already created")

    db_path = os.path.join(root, os.path.basename(root) + "-crh.db")

    database.init(db_path)

    if reset:
        database.drop_tables([FileHash, Definition], safe=True)

    database.create_tables([FileHash, Definition], safe=True)

###################################
# Project
###################################

class Project:
    AVAIL_EXTS  = ["*.c", "*.h", "*.cpp", "*.hpp", "*.cc"]
    SOURCE_EXTS = ["*.c", "*.cpp", "*.cc"]
    HEADER_EXTS = ["*.h", "*.hpp"]

    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.files = []
        self.source_files = []
        self.header_files = []
        self.modified_files = []

    def get_files(self, reset=False):
        if self.files and not reset:
            return self.files

        for path, dirs, files in os.walk(self.root):
            path = os.path.relpath(path, self.root)
            for ext in Project.AVAIL_EXTS:
                self.files += [os.path.normpath(os.path.join(path, filename))
                                      for filename in fnmatch.filter(files, ext)]

        self.files = list(set(self.files))

        return self.files

    def get_source_files(self, reset=False):
        if self.source_files and not reset:
            return self.source_files

        for ext in Project.SOURCE_EXTS:
            self.source_files += [path for path in fnmatch.filter(self.get_files(reset), ext)]

        return self.source_files

    def get_header_files(self, reset=False):
        if self.header_files and not reset:
            return self.header_files

        for ext in Project.HEADER_EXTS:
            self.header_files += [path for path in fnmatch.filter(self.get_files(reset), ext)]

        return self.header_files

    def get_modified_files(self, reset=False):
        if self.modified_files and not reset:
            return self.modified_files

        for path in self.get_files():
            new_mtime = os.path.getmtime(os.path.join(self.root, path))
            new_hash  = hashlib.md5(str(new_mtime).encode('utf-8')).hexdigest()

            query = FileHash.select().where(FileHash.path == path)
            count = query.count()

            if count >= 2:
                raise Exception("Duplicated hash found")

            if count == 0:
                FileHash.create(path=path, hash=new_hash)
                self.modified_files += [path]
                continue

            old_hash = query.first().hash
            if old_hash != new_hash:
                FileHash.create(path=path, hash=new_hash)
                self.modified_files += [path]

        return self.modified_files

    def get_hierarchy(self, path=None):
        path = self.root if path is None else path

        data = {'name': os.path.basename(path)}
        data['id'] = os.path.relpath(path, self.root)

        if os.path.isdir(path):
            data['children'] = []
            contain = False
        
            for x in os.listdir(path):
                if not os.path.isdir(os.path.join(path, x)):
                    continue
                ret_val, contain_codes = self.get_hierarchy(os.path.join(path, x))
                contain = contain or contain_codes
                data['children'] += ret_val
           
            for x in os.listdir(path):
                if os.path.isdir(os.path.join(path, x)):
                    continue
                ret_val, contain_codes = self.get_hierarchy(os.path.join(path, x))
                contain = contain or contain_codes
                data['children'] += ret_val
        
            if contain:
                return [data], True
            else:
                return [], False
        else:
            ext = os.path.splitext(path)[1]
            if ext in [".c", ".h"]:
                return [data], True
            else:
                return [], False

    def read_file(self, path):
        encoding = "utf-8"

        path = os.path.join(self.root, path)

        try:
            with open(path, encoding=encoding, mode="r") as f:
                content = f.read()
                return content
        except UnicodeDecodeError:
            with open(path, mode="rb") as f:
                bin_content = f.read()
                encoding = chardet.detect(bin_content)['encoding']
                content = bin_content.decode(encoding)
                return content
        except:
            raise

    def search_file(self, filename):
        result = []

        for path in self.get_files():
            basename = os.path.basename(path)
            
            if basename != filename:
                continue

            result.append(path)

        return result


###################################
# Analyzer
###################################

class Analyzer:
    DEFINITION_BUFFER_SIZE = 50

    def __init__(self, proj):
        self.proj = proj
        self.definition_buffer = []
        self.analyzed_definition = False

    def analyze_definition(self):
        if self.analyzed_definition:
            return

        for i, path in enumerate(self.proj.get_modified_files()):
            Definition.delete().where(Definition.path == path).execute()

            index = clang.cindex.Index.create()

            code = self.proj.read_file(path)
            # code = self._strip_header(code)

            tu = index.parse(path,
                             unsaved_files=[(path, code)],
                             options=clang.cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)

            self._search_definition(path, tu.cursor)

            if self.definition_buffer:
                with database.transaction():
                    Definition.insert_many(self.definition_buffer).execute()
                self.definition_buffer = []

        self.analyzed_definition = True

    def _search_definition(self, path, node):
        constraint = node.is_definition()
        constraint = constraint and node.kind.name != "STATIC_ASSERT"
        constraint = constraint and node.location.file and node.location.file.name == path
        constraint = constraint or node.kind == clang.cindex.CursorKind.MACRO_DEFINITION

        # ensure that the parent of the node is not `Proptotype Declaration`
        if node.kind.name == "PARM_DECL":
            constraint = node.semantic_parent.is_definition()

        if constraint:
            record = dict(path=path,
                          name=node.spelling,
                          kind=node.kind.name,
                          type=node.type.spelling,
                          line=node.location.line)

            self.definition_buffer.append(record)

            if len(self.definition_buffer) >= Analyzer.DEFINITION_BUFFER_SIZE:
                with database.transaction():
                    Definition.insert_many(self.definition_buffer).execute()
                self.definition_buffer = []

        for child in node.get_children():
            self._search_definition(path, child)

    def analyze_call_graph(self, path, root_func=None):
        self.analyze_definition()

        path = os.path.join(self.proj.root, path)
        index = clang.cindex.Index.create()

        code = self.proj.read_file(path)
        code = self._strip_header(code, remain_project_header=True)

        tu = index.parse(path, unsaved_files=[(path, code)])
        return list(set(self._generate_call_graph(tu.cursor, root_func)))

    def _generate_call_graph(self, node, root_func, caller=None):
        if node.is_definition() and node.kind.name == "FUNCTION_DECL":
            caller = node.spelling

            if root_func and caller != root_func:
                return []

        ret_val = set()

        if node.kind.name == "CALL_EXPR":
            callee = node.spelling
            records = Definition.select().where(Definition.name == callee).execute()

            for record in records:
                if record.kind != "FUNCTION_DECL":
                    continue
                ret_val.add((caller, callee))
                break

        ret_val = list(ret_val)

        for child in node.get_children():
            ret_val += self._generate_call_graph(child, root_func, caller)

        return ret_val

    def _strip_header(self, code, remain_project_header=False):
        code = re.sub(r'#include\s*<.+>', '', code)

        if not remain_project_header:
            code = re.sub(r'#include\s*".+"', '', code)

        return code
