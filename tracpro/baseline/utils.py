import numpy


def chart_baseline(baselineterm, regions, region_selected):
    """ Returns data that is used to build context for a baseline chart """
    baseline_dict, baseline_dates_dict = baselineterm.get_baseline(regions, region_selected)
    follow_ups, follow_up_dates_dict, all_regions = baselineterm.get_follow_up(regions, region_selected)

    # Create a list of all dates for this poll
    # Example: date_list =  ['09/01', '09/02', '09/03', ...]
    dates = []
    for region in follow_up_dates_dict:
        dates += follow_up_dates_dict[region]  # concatenate all the regional follow up dates
    dates = list(set(dates))  # get the list of distinct follow up dates
    dates.sort()  # sort the list of follow up dates
    date_list = []
    for date in dates:
        date_formatted = date.strftime('%m/%d')
        date_list.append(date_formatted)

    # Loop through all regions to create a list of baseline values over time
    # Example: {'Kampala': {'values': [100, 100, 120, 120,...] } }
    all_baselines = []
    for region in baseline_dict:
        baseline_list_all_dates = []
        baseline_list = baseline_dict[region]["values"]
        current_baseline = float(baseline_list[0])
        all_baselines.append(current_baseline)
        for date in dates:
            # If the date has a new baseline, add it to the list of baselines
            if date in baseline_dates_dict[region]:
                current_baseline = float(baseline_list[baseline_dates_dict[region].index(date)])
            baseline_list_all_dates.append(current_baseline)
        baseline_dict[region]["values"] = baseline_list_all_dates
    baseline_mean = round(numpy.mean(all_baselines), 5)
    baseline_std = round(numpy.std(all_baselines), 5)

    # Reformat the values lists to remove the Decimal()
    # Example in:  {'Kampala': {'values': [Decimal(100), Decimal(100)...] } }
    #         out: {'Kampala': {'values': [100, 100...] } }
    answers_dict = {}
    all_follow_ups = []
    for region in follow_ups:
        follow_up_list_all_dates = []
        follow_up_list = follow_ups[region]["values"]
        for date in dates:
            # If the date has a follow up, include it. If this date does not, mark it as 0
            if date in follow_up_dates_dict[region]:
                current_follow_up = float(follow_up_list[follow_up_dates_dict[region].index(date)])
                all_follow_ups.append(current_follow_up)
            else:
                current_follow_up = 0
            follow_up_list_all_dates.append(current_follow_up)
        answers_dict[region] = {}
        answers_dict[region]["values"] = follow_up_list_all_dates

    follow_up_mean = round(numpy.mean(all_follow_ups), 5)
    follow_up_std = round(numpy.std(all_follow_ups), 5)

    return (answers_dict, baseline_dict, all_regions, date_list,
            baseline_mean, baseline_std, follow_up_mean, follow_up_std)
