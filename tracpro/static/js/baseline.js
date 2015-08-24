$(function() {
    $("input[class^='datepicker']").datepicker();

    // Display/hide question if poll is selected
    if (!$("#id_baseline_poll").val()) {
        $("#id_baseline_question").closest(".form-group").hide();
    }
    $("#id_baseline_poll").change(function() {
      if($(this).val()) {
        $("#id_baseline_question").closest(".form-group").show();
      }
      else {
        $("#id_baseline_question").closest(".form-group").hide();
      }
    });

    // Display/hide question if poll is selected
    if (!$("#id_follow_up_poll").val()) {
        $("#id_follow_up_question").closest(".form-group").hide();
    }
    $("#id_follow_up_poll").change(function() {
      if($(this).val()) {
        $("#id_follow_up_question").closest(".form-group").show();
      }
      else {
        $("#id_follow_up_question").closest(".form-group").hide();
      }
    });
});
