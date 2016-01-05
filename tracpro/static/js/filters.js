$(function() {
  /* Initialize date fields.*/
  $("input[class^='datepicker']").datepicker();

  /* Update text on filter toggle button. */
  $('#filters').on('show.bs.collapse', function() {
    $('#toggle-filters').text('Hide filters...');
  });
  $('#filters').on('hide.bs.collapse', function() {
    $('#toggle-filters').text('Show filters...');
  });

  /* Don't submit unused fields. */
  $('.filter-form #id_date_range').on('change blur', function() {
    var show_dates = $(this).val() === 'other';
    $('#filter-dates').toggleClass('hidden', !show_dates);
    $('#filter-dates').find('input').prop('disabled', !show_dates)
  }).blur();
});
