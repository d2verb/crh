<!doctype html>
<html lang="ja">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">

	<title>Code Reading Helper</title>

	<link rel="stylesheet" type="text/css" href="{{ get_url('static', path='css/reset.css')  }}">
	<link rel="stylesheet" type="text/css" href="{{ get_url('static', path='css/monokai.css') }}">
	<link rel="stylesheet" type="text/css" href="{{ get_url('static', path='css/jqtree.css') }}">
	<link rel="stylesheet" type="text/css" href="{{ get_url('static', path='css/main.css') }}">
	<link rel="stylesheet" type="text/css" href="{{ get_url('static', path='css/font-awesome.min.css') }}">

	<script type="text/javascript" src="{{ get_url('static', path='js/jquery.js' ) }}"></script>
	<script type="text/javascript" src="{{ get_url('static', path='js/tree.jquery.js' ) }}"></script>

</head>
<body>
	<div class="flexbox">
		<section class="exploer scrollable">
      <ul class="exploer-menu">
        <li class="project-menu selected">Project</li>
        <li class="bookmarks-menu">Bookmarks</li>
        <li class="memo-menu">Memo</li>
      </ul>
      <div class="project-pane">
        <%
        import os
        project_name = os.path.basename(project.root)
        first_code   = project.get_files()[0]
        %>
        <div class="project-name label">{{ project_name }}</div>
        <div class="directory-tree" data-url="/tree"></div>
      </div>
      <div class="bookmarks-pane" style="display: none;">
        <div class="label bookmarks-pane-icon"><i class="fa fa-bookmark" aria-hidden="true"></i></div>
        <ul class="bookmarks">
        </ul>
      </div>
      <div class="memo-pane" style="display: none;">
        <div class="label bookmarks-pane-icon"><i class="fa fa-pencil" aria-hidden="true"></i></div>
        <span class="memo-name"></span>
        <textarea class="memo-area"></textarea>
        <br>
        <button class="save-button">Save</button>
        <button class="delete-button">Delete</button>
        <span class="memo-info"></span>
      </div>
		</section>

		<section class="viwer scrollable">
      <div class="codearea">
      </div>
      <ul class="toolbar">
        <li class="add-to-bookmarks"><i class="fa fa-star" aria-hidden="true"></i></li>
        <li class="goto-prev"><i class="fa fa-arrow-left" aria-hidden="true"></i></li>
        <li class="goto-next"><i class="fa fa-arrow-right" aria-hidden="true"></i></li>
      </ul>
		</section>

		<section class="analyzer">
			<div class="label">Definition Search</div>
			<form class="search-box" method="post" action="/search">
				<input type="text" class="search-input" name="pattern" placeholder="SEARCH">
				<input type="submit" class="search-button" value="search">
				<p class="options">
					<input type="checkbox" name="partial" checked="checked"><span class="option-text">partial</span>
					<input type="checkbox" name="samefile"><span class="option-text">same file</span>
					<select name="kind">
						<option value="*">*</option>
						<option value="STRUCT_DECL">struct</option>
						<option value="FIELD_DECL">struct field</option>
						<option value="UNION_DECL">union</option>
						<option value="ENUM_DECL">enum</option>
						<option value="ENUM_CONSTANT_DECL">enum constant</option>
						<option value="FUNCTION_DECL">function</option>
						<option value="VAR_DECL">variable</option>
						<option value="PARM_DECL">function parameter</option>
						<option value="TYPEDEF_DECL">typedef</option>
					</select>
				</p>
			</form>
			<div class="label">Search Results</div>
			<div class="results scrollable">
				<table class="results-table">
					<tr>
						<th scope="col">LINE</th>
						<th scope="col">PATH</th>
						<th scope="col">NAME</th>
						<th scope="col">KIND</th>
					</tr>
				</table>
			</div>
		</section>
	</div>
	<script type="text/javascript" src="{{ get_url('static', path='js/main.js' ) }}"></script>
</body>
<html>
