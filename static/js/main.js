var now_path = null,
    hist = null;
var cnt = 0;
$('.bookmars-pane').hide();

/*********************************
* History Tree
**********************************/

var historyTreeNode = function(prev, next, path, line) {
  // if (line == undefined)
  //   this.line = 1;
  // else
  this.line = line;
  this.path = path;
  this.prev = prev;
  this.next = next;
}

var historyTree = function() {
  this.now_hist = new historyTreeNode(null, null, null, null);
}

historyTree.prototype.get_now_hist = function() {
  return this.now_hist;
}

historyTree.prototype.get_prev_hist = function() {
  return this.now_hist.prev;
}

historyTree.prototype.get_next_hist = function() {
  return this.now_hist.next;
}

historyTree.prototype.goto_prev_hist = function() {
  if (this.now_hist.prev != null)
    this.now_hist = this.now_hist.prev;
}

historyTree.prototype.goto_next_hist = function() {
  if (this.now_hist.next != null)
    this.now_hist = this.now_hist.next;
}

historyTree.prototype.add_new_hist = function(path, line) {
  // if (line == undefined)
  //   line = 1;

  this.now_hist.next = null;
  this.now_hist.next = new historyTreeNode(this.now_hist, null, path, line);

  this.goto_next_hist();
}

hist = new historyTree();

$('.goto-prev').click(function () {
  if (hist.get_prev_hist() != null) {
    var path = hist.get_prev_hist().path;
    var line = hist.get_prev_hist().line;
    update_viewr(path, line, false);
    hist.goto_prev_hist();
  }
});

$('.goto-next').click(function () {
  if (hist.get_next_hist() != null) {
    var path = hist.get_next_hist().path;
    var line = hist.get_next_hist().line;
    update_viewr(path, line, false);
    hist.goto_next_hist();
  }
});

/***********************************
* Update Code Area and Project Pane
************************************/

function update_viewr(path, line, from_click) {
	path = path.replace(/^\/+/, '');
	var url = "/code/" + path;
	
	$.get(url, {line: line}, function (data) {
		$(".codearea").empty();
		$(".codearea").append(data);

		if (line !== undefined) {
			$('a[href="#line-'+line+'"]')[0].click();
			$('a[href="#line-'+line+'"]').css('display', 'inline-block');
			$('a[href="#line-'+line+'"]').css('width', '100%');
			$('a[href="#line-'+line+'"]').css('background-color', '#89887e');
		}
	});

	now_path = path;

  if (!from_click) {
    var tree = $('.directory-tree');
    var target_node = tree.tree('getNodeById', now_path);
    tree.tree('selectNode', target_node);
  }

  var inLocalStorage = localStorage.getItem(path);
  if (inLocalStorage) {
    $('.add-to-bookmarks').addClass("bookmarked");
  } else {
    $('.add-to-bookmarks').removeClass("bookmarked");
  }

  renderMemoPane();
}

$('.directory-tree').tree({
	closedIcon: " ",
	openedIcon: " "
});

$('.directory-tree').bind(
	'tree.click',
	function(event) {
  	if (event.node.children.length >= 1) {
  		$('.directory-tree').tree('toggle', event.node);
  		return;
  	}
  	update_viewr(event.node.id, undefined, true);
    hist.add_new_hist(event.node.id)
  }
);

/*******************
* Search Process
*******************/

function table_entry_click_handler(path, line) {
  update_viewr(path, line, false);
  hist.add_new_hist(path, line);
}

$('form').submit(function (event) {
	event.preventDefault();
	var f = $(this);
	$.ajax({
		url: f.prop('action'),
		type: f.prop('method'),
		data: f.serialize(),
		timeout: 10000,
		dataType: 'json'
	})
	.done(function (data) {
		var content = "<tr><th scope=\"col\">LINE</th><th scope=\"col\">PATH</th><th scope=\"col\">NAME</th><th scope=\"col\">KIND</th></tr>";
		var rest_data = [];

		for (var i = 0; i < data.length; i++) {

			content += "<tr onclick=\"table_entry_click_handler('" + data[i].path + "', " + data[i].line + ");\" class=\"data\">";
			content += "<td>" + data[i].line + "</td>";
			content += "<td>" + data[i].path + "</td>";
			content += "<td>" + data[i].name + "</td>";
			content += "<td>" + data[i].kind + "</td>";
			content += "</tr>";
		}

		$(".results-table").empty();
		$(".results-table").append(content);
	})
	.always(function( data ) {
	});
});

/**************************
* Explorer Menu Toggler
***************************/
$('.project-menu').click(function () {
  $('.bookmarks-menu').removeClass("selected");
  $('.memo-menu').removeClass("selected");
  $(this).addClass("selected");
  $('.bookmarks-pane').hide();
  $('.memo-pane').hide();
  $('.project-pane').show();
});

$('.bookmarks-menu').click(function () {
  $('.project-menu').removeClass("selected");
  $('.memo-menu').removeClass("selected");
  $(this).addClass("selected");
  $('.bookmarks-pane').show();
  $('.project-pane').hide();
  $('.memo-pane').hide();
  renderBookmarksPane();
});

$('.memo-menu').click(function () {
  $('.project-menu').removeClass("selected");
  $('.bookmarks-menu').removeClass("selected");
  $(this).addClass("selected");
  $('.memo-pane').show();
  $('.bookmarks-pane').hide();
  $('.project-pane').hide();
  renderMemoPane();
});


/******************************
* Bookmarking Process
*******************************/
function highlightSelectedBookmark() {
  var num  = $('.bookmark-item').length;

  for (var i = 0; i < num; i++) {
    var text = $('.bookmark-item')[i].textContent;
    if (text == now_path) {
      $($('.bookmark-item')[i]).addClass("bookmark-item-selected");
    } else {
      $($('.bookmark-item')[i]).removeClass("bookmark-item-selected");
    }
  }
}

function renderBookmarksPane() {
  $('.bookmarks').empty();

  bookmarkedItems = Object.keys(localStorage);
  bookmarkedItemsLength = bookmarkedItems.length;

  for (var i = 0; i < bookmarkedItemsLength; i++) {
    var item = bookmarkedItems[i];
    if (item.endsWith("-memo"))
      continue;
    content = "<li class='bookmark-item'>" + item + "</li>"
    $('.bookmarks').append(content);
  }

  $('.bookmark-item').click(function () {
    var path = $(this)[0].textContent;

    update_viewr(path);
    highlightSelectedBookmark();
  });
  
  highlightSelectedBookmark();
}

$('.add-to-bookmarks').click(function () {
  if (now_path == null)
    return;
  inLocalStorage = localStorage.getItem(now_path);
  if (inLocalStorage) {
    localStorage.removeItem(now_path);
    $(this).removeClass('bookmarked');
  } else {
    localStorage.setItem(now_path, Object.keys(localStorage).length);
    $(this).addClass('bookmarked');
  }
  renderBookmarksPane();
});


/*************************************
* Memo Pane Process
**************************************/
function renderMemoPane() {
  var memo = localStorage.getItem(now_path + "-memo");
  if (memo) {
    $('.memo-area')[0].value = memo;
  } else {
    $('.memo-area')[0].value = "";
  }
  $('.memo-info').empty();
  $('.memo-name').empty();
  $('.memo-name').text(now_path);
}

$('.memo-pane').ready(function () {
  $('.save-button').click(function () {
    var newMemo = $('.memo-area')[0].value;
    if (now_path) {
      localStorage.setItem(now_path + "-memo", newMemo);
    }
    $('.memo-info').empty();
    $('.memo-info').append('saved');
  });

  $('.delete-button').click(function () {
    if (now_path) {
      localStorage.removeItem(now_path + "-memo");
    }
    renderMemoPane();
    $('.memo-info').empty();
    $('.memo-info').append('deleted');
  });
});
