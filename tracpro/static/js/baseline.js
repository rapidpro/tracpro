$(function() {
        $("input[class^='datepicker']").datepicker();

        // Display/hide question if poll is selected
        if (!$("#id_baseline_poll").val()) {
            $("#id_baseline_question").parent().parent().hide();
        }
        $("#id_baseline_poll").on("change", function() {
          if(this.value) {
            $("#id_baseline_question").parent().parent().show();
          }
          else {
            $("#id_baseline_question").parent().parent().hide();
          }
        });

        // Display/hide question if poll is selected
        if (!$("#id_follow_up_poll").val()) {
            $("#id_follow_up_question").parent().parent().hide();
        }
        $("#id_follow_up_poll").on("change", function() {
          if(this.value) {
            $("#id_follow_up_question").parent().parent().show();
          }
          else {
            $("#id_follow_up_question").parent().parent().hide();
          }
        });
    });
