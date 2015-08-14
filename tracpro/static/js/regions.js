$(function() {
    /* Initialize the hierarchical tree table in the expanded state. */
    $(".treetable").treetable({
        expandable: true,
        expanderTemplate: '<a href="#"><span class="glyphicon"></span></a>',
        initialState: "expanded"
    });
});
