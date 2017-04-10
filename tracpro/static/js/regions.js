$(function() {
    var EDIT_REGIONS_HELP = "Edit panel hierarchy by dragging and " +
                            "dropping table rows. Click 'Save Panels' " +
                            "when changes are complete.";

    // Identifier for any message related to editing regions.
    var EDIT_REGIONS_MESSAGE = "edit-regions-message";

    // The first row is a dummy that exists so that the user can drag
    // other regions to the top level.
    var ALL_ROWS = $(".treetable tbody tr.region");
    var REGION_ROWS = ALL_ROWS.not(":first-child");

    /* Per Django documentation, to get CSRF cookie for AJAX post. */
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /* Add user message to the top of the page. */
    var addUserMessage = function(id, type, message, hideClose) {
        clearUserMessage(id);  // Remove previous messages that used this ID.
        msgDiv = $("<div>").attr("id", id);
        msgDiv.addClass("alert alert-" + type);
        msgDiv.html(message)
        if (!hideClose) {
            close = $("<a>").attr("href", "#")
            close.addClass("close").attr("data-dismiss", "alert")
            close.html("×");
            msgDiv.prepend(close);
        }
        $("#user-messages").append(msgDiv);
    }

    /* Remove user message from the top of the page. */
    var clearUserMessage = function(id) {
        $("#" + id).remove();
    }

    /* Allow user to edit regions. */
    $("#edit-regions").click(function () {
        clearUserMessage(EDIT_REGIONS_MESSAGE);

        /* Display only the "Save Regions" button. */
        $("#region-actions .btn.action").addClass("hidden");
        $("#save-regions").removeClass("hidden");

        /* Show user help message. */
        addUserMessage(EDIT_REGIONS_MESSAGE, "info", EDIT_REGIONS_HELP, true);

        /* Show boundary selectors. */
        REGION_ROWS.find('.value-boundary .value').addClass('hidden');
        REGION_ROWS.find('.value-boundary .boundary-select').removeClass('hidden');

        /* Enable drag-and-drop. */
        $(".list_groups_region").addClass("edit-mode");
        REGION_ROWS.draggable("enable");
        ALL_ROWS.droppable("enable");
    })

    /* Save region edits to server. */
    $("#save-regions").click(function() {
        /* Disable drag-and-drop. */
        REGION_ROWS.draggable("disable");
        ALL_ROWS.droppable("disable");

        /* Display only the "Saving Regions..." button. */
        $("#region-actions .btn.action").addClass("hidden");
        $("#saving-regions").removeClass("hidden");

        updateRegionsOnServer();
    });

    /* Display success message & allow user to edit again. */
    var saveRegionsSuccess = function(message) {
        addUserMessage(EDIT_REGIONS_MESSAGE, "success", message);

        /* Hide boundary selectors. */
        REGION_ROWS.find('.value-boundary .boundary-select').addClass('hidden');
        REGION_ROWS.find('.value-boundary .value').removeClass('hidden');

        /* Display only the "Edit Regions" button. */
        $(".list_groups_region").removeClass("edit-mode");
        $("#region-actions .btn.action").addClass("hidden");
        $("#edit-regions").removeClass("hidden");
    }

    /* Display error message & maintain "editing" state. */
    var saveRegionsFailure = function(message) {
        addUserMessage(EDIT_REGIONS_MESSAGE, "error", message);

        /* Display only the "Save Regions" button. */
        $("#region-actions .btn.action").addClass("hidden");
        $("#save-regions").removeClass("hidden");
    }

    /* Send the updated regions to the server. */
    var updateRegionsOnServer = function() {
        var regionParents = {};  // region id -> (parent id, boundary id)
        $(".list_groups_region tbody").find("tr:not(:first-child)").each(function(i) {
            var regionId = $(this).data("ttId");
            var parentId = $(this).data("ttParentId") || null;
            var boundaryId = $(this).find(".boundary-select").val() || null;
            regionParents[regionId] = [parentId, boundaryId];
        });

        $.ajax({
            data: {
                csrfmiddlewaretoken: getCookie('csrftoken'),
                data: JSON.stringify(regionParents)
            },
            dataType: "json",
            type: "POST",
            url: $(".list_groups_region").data("updateRegionsUrl")
        }).done(function(data, status, xhr) {
            if (data['success']) {
                saveRegionsSuccess(data['message']);
            } else {
                message = "<strong>An error occurred while saving the " +
                          "panel changes:</strong> " + data["message"];
                saveRegionsFailure(message);
            }
        }).fail(function() {
            var message = "An error has occurred and your changes were not " +
                          "saved. Please try again later.";
            saveRegionsFailure(message);
        });
    };

    /* Allow dragging table rows that represent regions. */
    REGION_ROWS.draggable({
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
    REGION_ROWS.draggable("disable");  // Enable by clicking #edit-regions.

    /* Allow dropping regions onto any table row. */
    ALL_ROWS.droppable({
        accept: REGION_ROWS,
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
    ALL_ROWS.droppable("disable");  // Enable by clicking #edit-regions.

    /* Initialize the hierarchical tree table in the expanded state. */
    $(".treetable").treetable({
        expandable: true,
        expanderTemplate: '<a href="#"><span class="glyphicon"></span></a>',
        initialState: "expanded",
        onInitialized: function() {
            var table = $(this.table);
            table.find("tr").removeClass("hidden");
            table.find("tr.loading-text").remove();
        }
    });

    $('td.value-boundary select').change(function() {
        var self = $(this);
        var label = self.find(':selected').text();
        self.closest('.value-boundary').find('.value').text(label);
    });
});
