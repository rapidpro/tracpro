$(function() {
    $("input[class^='datepicker']").datepicker();

    $("#id_baseline_poll").change(function() {
      if($(this).val()) {
        $("#id_baseline_question").closest(".form-group").show();
      }
      else {
        $("#id_baseline_question").closest(".form-group").hide();
      }
    });

    $("#id_follow_up_poll").change(function() {
      if($(this).val()) {
        $("#id_follow_up_question").closest(".form-group").show();
      }
      else {
        $("#id_follow_up_question").closest(".form-group").hide();
      }
    });

    $("#id_follow_up_poll,#id_baseline_poll").change();
});
