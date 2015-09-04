$(function() {
  /* Set indentation in sub-menus.
   *
   * Using the indenter allows every menu item (regardless of depth)
   * to be clickable over the full width of the menu.
   */
  $(".submenu").each(function(i, submenu) {
    $(submenu).find(">li").each(function(i, li) {
      // Progressively increase indentation with each pass over the menu item.
      var indenter = $(li).find(".indenter");
      indenter.css("width", parseInt(indenter.css("width")) + 20 + "px");
    });
  });

  $(".toggle-subregions").click(function(e) {
    $("#toggle-subregions-form").submit();
    return false;
  });
});
