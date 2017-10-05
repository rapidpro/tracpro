$(function() {
    /* Initialize date fields. */
    $(".filter-form input[class^='datepicker']").datepicker({
        changeMonth: true,
        changeYear: true,
        selectOtherMonths: true,
        showOtherMonths: true,
        yearRange: "2013:" + new Date().getFullYear()
    });

    /* Update button text when filter form display is toggled. */
    $('#filters').on('show.bs.collapse', function() {
        $('#toggle-filters').text('Hide filters...');
    });
    $('#filters').on('hide.bs.collapse', function() {
        $('#toggle-filters').text('Show filters...');
    });

    /* Don't show or submit custom date fields if they are not needed. */
    $('.filter-form #id_date_range').on('change', function() {
        var showDates = $(this).val() === 'custom';
        $('#filter-dates').toggleClass('hidden', !showDates);
        $('#filter-dates').find('input').prop('disabled', !showDates);
    }).change();

    /* Don't submit empty form fields. */
    $('.filter-form').on('submit', function() {
        $(this).find('input,select').each(function(i, item) {
          var self = $(this);
          if (!self.val()) {
            self.prop('disabled', true);
          }
        });
        return true;
    });
});
