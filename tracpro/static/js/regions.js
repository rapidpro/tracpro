$(function() {
    /* Initialize the hierarchical tree table in the expanded state. */
    $(".treetable").treetable({
        expandable: true,
        expanderTemplate: '<a href="#"><span class="glyphicon"></span></a>',
        initialState: "expanded"
    });

    /* Allow dragging table rows. */
    $(".treetable tbody tr").not(":first-child").draggable({
        containment: "document",
        cursor: "move",
        delay: 200,  // Avoid triggering drag when expanding/collapsing.
        helper: function() {
            var cell = $(this).find("td:first-child");
            var indenterPadding = parseInt(cell.find(".indenter").css("padding-left"));
            var el = cell.find(".value").clone()
            // Pad to be approximately in line with original cell.
            el.css("padding-left", 34 + indenterPadding + "px");
            return el;
        },
        opacity: 0.75,
        refreshPositions: true,  // Necessary when nodes expand while dragging.
        revert: "invalid",
        revertDuration: 300,
        scroll: true,
        start: function(e, ui) {
            $(this).addClass("selected");
        },
        stop: function(e, ui) {
            $(this).removeClass("selected");
        }
    });

    /* Allow dropping table rows. */
    $(".treetable tbody tr").droppable({
        accept: ".treetable tbody tr.region",
        drop: function(e, ui) {
            var table = $(this).closest(".treetable");
            var toMoveNode = table.treetable("node", ui.draggable.data("ttId"));
            var newParentNode = table.treetable("node", $(this).data("ttId"));
            table.treetable("expandNode", newParentNode.id);
            table.treetable("move", toMoveNode.id, newParentNode.id);
            table.treetable("sortBranch", newParentNode);
        },
        hoverClass: "hovered",
        over: function(e, ui) {
            var toMove = ui.draggable;
            var candidateParent = $(this);
            if (toMove != candidateParent && !candidateParent.is(".expanded")) {
                var table = $(this).closest(".treetable");
                table.treetable("expandNode", candidateParent.data("ttId"));
            }
        }
    });
});
