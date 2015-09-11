def chart_baseline(baselineterm, regions, region_selected):
    """ Returns data that is used to build context for a baseline chart """
    baseline_dict, baseline_dates = baselineterm.get_baseline(regions, region_selected)
    follow_ups, dates, all_regions = baselineterm.get_follow_up(regions, region_selected)

    # Create a list of all dates for this poll
    # Example: date_list =  ['09/01', '09/02', '09/03', ...]
    date_list = []
    for date in dates:
        date_formatted = date.strftime('%m/%d')
        date_list.append(date_formatted)

    # Loop through all regions to create a list of baseline values over time
    # Example: {'Kampala': {'values': [100, 100, 120, 120,...] } }
    for region in baseline_dict:
        baseline_list_all_dates = []
        baseline_list = baseline_dict[region]["values"]
        current_baseline = float(baseline_list[0])
        for date in dates:
            if date in baseline_dates:
                current_baseline = float(baseline_list[baseline_dates.index(date)])
            baseline_list_all_dates.append(current_baseline)
        baseline_dict[region]["values"] = baseline_list_all_dates

    # Reformat the values lists to remove the Decimal()
    # Example in:  {'Kampala': {'values': [Decimal(100), Decimal(100)...] } }
    #         out: {'Kampala': {'values': [100, 100...] } }
    answers_dict = {}
    for follow_up in follow_ups:
        answers_dict[follow_up] = {}
        answers_dict[follow_up]["values"] = [float(val) for val in follow_ups[follow_up]["values"]]

    return answers_dict, baseline_dict, all_regions, date_list
