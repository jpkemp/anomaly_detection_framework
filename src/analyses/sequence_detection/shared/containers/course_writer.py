from datetime import timedelta
import xlsxwriter

class WriteProviderCourses:
    def __init__(self, filename, provider_course_rules, cost, rank, courses, filtered_rules, rare_item_proportions, cost_breakdown):
        provider = provider_course_rules.id
        with xlsxwriter.Workbook(filename) as xl:
            self.write_provider_episodes(xl, provider, cost, rank, courses)
            self.write_provider_unusual_rules(xl, provider_course_rules, filtered_rules)
            self.write_rare_items(xl, rare_item_proportions)
            self.write_cost_breakdown(xl, cost_breakdown)

    def write_provider_episodes(self, xl, provider, cost, rank, courses):
        ital = xl.add_format({'italic': True})
        bold = xl.add_format({'bold': True})
        bold_ital = xl.add_format({'bold': True, 'italic': True})
        flagged = xl.add_format({'bg_color': 'yellow'})
        double_flagged = xl.add_format({'font_color': 'red', 'bg_color': 'yellow'})
        sheet = xl.add_worksheet(f"Courses of treatment")
        sheet.write('A1', f"Provider:", bold)
        sheet.write('B1', provider)
        sheet.write('A2', "Potential recoverable costs:", bold)
        sheet.write('B2', cost)
        sheet.write('A3', "Number of courses:", bold)
        sheet.write('B3', len(courses))
        sheet.write('A5', "Courses", bold_ital)
        days = max(len(x.course.item_sequence.sequence) for x in courses)
        for col in range(1, days+1):
            sheet.write(5, col, f"Episode {col}", bold)

        row = 6
        for i, course in enumerate(courses):
            sequence = course.course.item_sequence.sequence
            sequence_timestamps = course.course.item_sequence.timestamps
            flagged_timestamps = course.flagged_timestamps
            doubled_flagged_timestamps = course.double_flagged_timestamps
            sheet.write(row, 0, "Patient ID:", ital)
            sheet.write(row, 1, course.course.patient_id)
            sheet.write(row+1, 0, "Course timestamps", ital)
            sheet.write(row+2, 0, "Course dates", ital)
            sheet.write(row+3, 0, "Course items", ital)
            for j, day in enumerate(sequence):
                col = j + 1
                tstamp = sequence_timestamps[j]
                date = course.course.start + timedelta(tstamp)
                sheet.write(row+1, col, tstamp, ital)
                sheet.write(row+2, col, date.strftime("%d-%b-%y"), ital)
                if j in flagged_timestamps:
                    if j in doubled_flagged_timestamps:
                        sheet.write(row+3, col, day, double_flagged)
                    else:
                        sheet.write(row+3, col, day, flagged)
                else:
                    sheet.write(row+3, col, day)
            row += 5

    def write_provider_unusual_rules(self, xl, provider_course_rules, filtered_rules):
        bold = xl.add_format({'bold': True})
        sheet = xl.add_worksheet(f"Provider flagged rules")
        sheet.write('A1', "Rule", bold)
        sheet.write('B1', "Replacement rule", bold)
        sheet.write('C1', "Provider proportion (%)", bold)
        row = 0
        col = 3
        for x in [25, 50, 75, 90, 95, 100]:
            sheet.write(row, col, f"Q{x} proportion (%)", bold)
            col += 1

        row=1
        for rule_name in provider_course_rules.rules:
            if rule_name in filtered_rules:
                rule = filtered_rules[rule_name]
                if provider_course_rules.id in rule.provider_order:
                    sheet.write(row, 0, rule_name)
                    sheet.write(row, 1, provider_course_rules.replaced_rules[rule_name])
                    idx = rule.provider_order.index(provider_course_rules.id)
                    sheet.write(row, 2, f"{rule.rates[idx] * 100:.2f}")
                    col = 3
                    for val in rule.quantiles.values():
                        sheet.write(row, col, f"{val * 100:.2f}")
                        col += 1
                    row += 1

    def write_rare_items(self, xl, rare_items):
        bold = xl.add_format({'bold': True})
        sheet = xl.add_worksheet("Rare items")
        sheet.write('A1', "Rare item", bold)
        sheet.write('B1', "Total proportion of courses with item (%)", bold)
        row=1
        for item, proportion in rare_items.items():
            sheet.write(row, 0, item)
            sheet.write(row, 1, f"{proportion * 100:.3f}")
            row += 1

    def write_cost_breakdown(self, xl, cost_breakdown):
        sorted_breakdown = cost_breakdown.most_common()
        bold = xl.add_format({'bold': True})
        sheet = xl.add_worksheet("Cost breakdown")
        sheet.write('A1', "Item", bold)
        sheet.write('B1', "Cost", bold)
        row = 0
        for item, cost in sorted_breakdown:
            row += 1
            sheet.write(row, 0, item)
            sheet.write(row, 1, cost)
