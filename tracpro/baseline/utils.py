import numpy


def chart_baseline(baselineterm, regions, region_selected):
    """ Returns data that is used to build context for a baseline chart """
    baseline_total, baseline_dates_list = baselineterm.get_baseline(regions, region_selected)
    follow_up_list, follow_up_dates_list, all_regions = baselineterm.get_follow_up(regions, region_selected)

    # Create a list of all dates for this poll
    # Example: date_list =  ['09/01', '09/02', '09/03', ...]
    dates = list(set(follow_up_dates_list))  # Get the list of distinct follow up dates
    dates.sort()  # Sort the list of follow up dates
    date_list = [date.strftime('%m/%d') for date in dates]

    # Format the baseline into a list of baselines ie [100, 110, 90,...]
    baseline_list = [float(baseline_total)] * len(dates)
    baseline_mean = float(baseline_total)
    baseline_std = 0

    follow_up_mean = round(numpy.mean(follow_up_list), 1)
    follow_up_std = round(numpy.std(follow_up_list), 1)

    return (follow_up_list, baseline_list, all_regions, date_list,
            baseline_mean, baseline_std, follow_up_mean, follow_up_std)
