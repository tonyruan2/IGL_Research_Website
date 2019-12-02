from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from flask_nav.elements import Navbar, Subgroup, View
from flask_nav import Nav
from bokeh.plotting import figure, output_file, show
from bokeh.embed import components
from bokeh.models import ColumnDataSource
from bokeh.models import HoverTool
from bokeh.models import Legend
import math
import random
from scipy.special import comb


def bernoulli_trial(success_probability, desired_successes, num_trials):
    if success_probability < 0 or success_probability > 1 or desired_successes < 0 or desired_successes > num_trials:
        raise ValueError
    failure_probability = 1 - success_probability
    desired_failures = num_trials - desired_successes
    return comb(num_trials, desired_successes) * (success_probability ** desired_successes) * (
            failure_probability ** desired_failures)


def bernoulli_trial_sum(success_probability, desired_probability, min_successes, num_trials, standardization):
    probability_sum = 0
    desired_successes = int(min_successes)
    while desired_successes <= num_trials:
        probability_sum += bernoulli_trial(success_probability, desired_successes, num_trials)
        desired_successes += 1
    if standardization == 'p=q':
        return math.sqrt(num_trials) * (probability_sum - 0.5)
    if standardization == 'p!=q':
        decay_rate = math.log10((1 - desired_probability) / (1 - success_probability)) + (desired_probability * math.log10((desired_probability * (1 - success_probability)) / (success_probability * (1 - desired_probability))))
        return math.sqrt(num_trials) * (probability_sum) * math.exp(decay_rate * num_trials)
    return probability_sum


def compute_model(process_prob, desired_numer, desired_denom, num_trials, standardization):
    try:
        current_trial_count = 1
        results = []
        desired_prob = desired_numer / desired_denom
        while current_trial_count <= num_trials:
            min_successes = math.ceil((desired_numer * current_trial_count) / desired_denom)
            long_term_prob = bernoulli_trial_sum(process_prob, desired_prob, min_successes, current_trial_count, standardization)
            results.append(long_term_prob)
            current_trial_count += 1
        return results
    except ValueError:
        return [0 for x in range(num_trials)]


def gcd(a, b):
    while (b != 0):
        tmp = b
        b = a % b
        a = tmp
    return a


def generate_color(periodicity_num, count, highlight):
    entries = ['#0000FF', '#800080', '#FF00FF', '#008000', '#00FFFF','#808000', '#FA8072', '#7DEE3A']

    if highlight == 'monotonicity':
        if periodicity_num < 8 or count < 8:
            return entries[count]

    if highlight == 'periodicity':
        if count < 8:
            return entries[count]

    entries = ['0', '1', '2', '3', '4', '5', '6', '7', '8', 'A', 'B', 'C', 'D', 'E', 'F']
    color = '#'
    while len(color) < 7:
        color += entries[random.randint(0, 15) - 1]
    return color


def create_model(process_prob, desired_numer, desired_denom, num_trials, highlight, lines, standardization):

    draw_lines = False
    if lines == 'include':
        draw_lines = True

    title = 'Probability Model'
    if highlight == 'monotonicity' or highlight == 'periodicity0' or highlight == 'periodicity1':
        if highlight == 'monotonicity':
            title += ' (' + highlight
        else:
            title += ' (' + 'periodicity'
        if lines == 'include':
            title += ', ' + 'lines drawn)'
        else:
            title += ')'
    else:
        if lines == 'include':
            title += ' (lines drawn)'

    if standardization != '':
        if standardization == 'p=q':
            title += ' [stdrd p = q]'
        elif standardization == 'p!=q':
            title += ' [stdrd p != q]'

    model = figure(plot_width=849,
                  plot_height=660,
                  x_range=(0, num_trials + (num_trials / 10)),
                  y_range=(0, 1.10),
                  x_axis_label='Trial count',
                  y_axis_label='Probability to achieve desired success',
                  title=title, tools='pan, wheel_zoom, reset, save',
                  active_drag='pan', active_scroll='wheel_zoom')

    model.sizing_mode = 'scale_both'
    model.background_fill_color = 'beige'

    model.border_fill_color = 'whitesmoke'
    model.min_border = 60

    model.title.text_font_size = '20pt'

    model.xaxis.axis_label_text_font_size = '18pt'
    model.xaxis.major_label_text_font_size = '16pt'

    model.yaxis.axis_label_text_font_size = '18pt'
    model.yaxis.major_label_text_font_size = '16pt'

    periodicity_num = int(desired_denom) / int(gcd(int(desired_numer), int(desired_denom)))
    periodicity_num = int(periodicity_num)

    if highlight == 'monotonicity' or highlight == 'periodicity0' or highlight == 'periodicity1':

        if highlight == 'monotonicity':
            count = 0
            while count < periodicity_num and count <= num_trials:
                trials = [x for x in range(count, num_trials + 1, periodicity_num) if x != 0 and x <= num_trials]
                probabilities = [bernoulli_trial_sum(process_prob, desired_numer / desired_denom, math.ceil((desired_numer * current_trial_count) / desired_denom), current_trial_count, standardization) for current_trial_count in trials]
                data = {'trial_count': trials,
                        'probability': probabilities}

                data_cds = ColumnDataSource(data)

                color = generate_color(periodicity_num, count, 'monotonicity')
                model.circle(x='trial_count',
                            y='probability',
                            source=data_cds,
                            size=10,
                            color=color)

                if draw_lines:
                    model.line(x='trial_count',
                            y='probability',
                            source=data_cds,
                            line_width=2, line_color=color)

                count += 1

            trials = [x + 1 for x in range(num_trials)]
            data = {'trial_count': trials,
                'probability': compute_model(process_prob, desired_numer, desired_denom, num_trials, standardization),
                'mod': [(x % periodicity_num) for x in trials]}

            data_cds = ColumnDataSource(data)

            hover_glyph = model.circle(x='trial_count',
                                      y='probability',
                                      source=data_cds,
                                      size=15,
                                      alpha=0,
                                      hover_fill_color='orange',
                                      hover_alpha=1)

            tooltips = [
                ('Trial count', '@trial_count'),
                ('Probability', '@probability'),
                ('Mod ' + str(periodicity_num), '@mod')
            ]

            model.add_tools(HoverTool(tooltips=tooltips, renderers=[hover_glyph]))

        else:
            count = 0
            while (count * periodicity_num) + 1 <= num_trials:
                trials = []
                if highlight == 'periodicity0':
                    trials = [x for x in range((count * periodicity_num), ((count + 1) * periodicity_num)) if x != 0 and x <= num_trials]
                else:
                    trials = [x for x in range((count * periodicity_num) + 1, ((count + 1) * periodicity_num) + 1) if x != 0 and x <= num_trials]
                probabilities = [bernoulli_trial_sum(process_prob, desired_numer / desired_denom, math.ceil((desired_numer * current_trial_count) / desired_denom), current_trial_count, standardization) for current_trial_count in trials]
                data = {'trial_count': trials,
                        'probability': probabilities}

                data_cds = ColumnDataSource(data)

                color = generate_color(periodicity_num, count, 'periodicity')
                model.circle(x='trial_count',
                            y='probability',
                            source=data_cds,
                            size=10,
                            color=color)

                if draw_lines:
                    model.line(x='trial_count',
                            y='probability',
                            source=data_cds,
                            line_width=2, line_color=color)

                count += 1

            trials = [x + 1 for x in range(num_trials)]
            data = {'trial_count': trials,
                'probability': compute_model(process_prob, desired_numer, desired_denom, num_trials, standardization),
                'mod': [(x % periodicity_num) for x in trials]}

            data_cds = ColumnDataSource(data)

            hover_glyph = model.circle(x='trial_count',
                                      y='probability',
                                      source=data_cds,
                                      size=15,
                                      alpha=0,
                                      hover_fill_color='orange',
                                      hover_alpha=1)

            tooltips = [
                ('Trial count', '@trial_count'),
                ('Probability', '@probability'),
                ('Mod ' + str(periodicity_num), '@mod')
            ]

            model.add_tools(HoverTool(tooltips=tooltips, renderers=[hover_glyph]))

    else:
        trials = [x + 1 for x in range(num_trials)]
        data = {'trial_count': trials,
            'probability': compute_model(process_prob, desired_numer, desired_denom, num_trials, standardization),
            'mod': [(x % periodicity_num) for x in trials]}

        data_cds = ColumnDataSource(data)

        if draw_lines:
            model.line(x='trial_count',
                    y='probability',
                    source=data_cds,
                    line_width=2, line_color='blue')

        model.circle(x='trial_count',
                y='probability',
                source=data_cds,
                size=10,
                color='blue')

        tooltips = [
            ('Trial count', '@trial_count'),
            ('Probability', '@probability'),
            ('Mod ' + str(periodicity_num), '@mod')
        ]

        hover_glyph = model.circle(x='trial_count',
                                  y='probability',
                                  source=data_cds,
                                  size=15,
                                  alpha=0,
                                  hover_fill_color='orange',
                                  hover_alpha=1)

        model.add_tools(HoverTool(tooltips=tooltips, renderers=[hover_glyph]))

    return model


def mono_model():
    # model for probabilities p, q in [0.01, 0.99] with increments of 0.01
    max_val = 99
    process_prob_list = [(x + 1) / 100 for x in range(max_val)]
    desired_numer_list = [(x + 1) for x in range(max_val)]
    desired_denom = 100

    is_monotone = [[True] * max_val for x in range(max_val)]

    first_index = 0
    second_index = 0

    using_tolerance = True
    tolerance = 0.0000000001
    #zero_bound = 0
    #one_bound = 1
    #half_upper_bound = 0.5
    #half_lower_bound = 0.5
    zero_bound = tolerance
    one_bound = 1 - tolerance
    half_upper_bound = 0.5 + tolerance
    half_lower_bound = 0.5 - tolerance

    for process_prob in process_prob_list:
        for desired_numer in desired_numer_list:
            periodicity_num = int(desired_denom) / int(gcd(int(desired_numer), int(desired_denom)))
            periodicity_num = int(periodicity_num)
            probabilities = compute_model(process_prob, desired_numer, desired_denom, 2 * periodicity_num, "")
            desired_prob = desired_numer / desired_denom

            is_process_desired_equal = process_prob == desired_prob
            is_monotonic_nonincreasing = process_prob < desired_prob
            is_monotonic_nondecreasing = process_prob > desired_prob

            for i in range(periodicity_num):
                second_point = i + periodicity_num

                if using_tolerance:
                    if probabilities[i] <= zero_bound or probabilities[i] >= one_bound:
                        break
                    if probabilities[second_point] <= zero_bound or probabilities[second_point] >= one_bound:
                        break
                    if abs(probabilities[second_point] - probabilities[i]) <= zero_bound:
                        break

                if is_process_desired_equal:
                    # nondecreasing
                    if probabilities[i] < 0.5:

                        if using_tolerance:
                            if probabilities[i] >= half_lower_bound:
                                if probabilities[i] >= half_upper_bound:
                                    is_monotone[first_index][second_index] = False
                                    break
                                break

                        first_monotonic_behavior = probabilities[second_point] >= probabilities[i]
                        if first_monotonic_behavior == False:
                            is_monotone[first_index][second_index] = False
                            break
                    else:
                        if using_tolerance:
                            if probabilities[i] <= half_upper_bound:
                                break
                        # nonincreasing
                        first_monotonic_behavior = probabilities[second_point] <= probabilities[i]
                        if first_monotonic_behavior == False:
                            is_monotone[first_index][second_index] = False
                            break

                elif is_monotonic_nonincreasing:
                    first_monotonic_behavior = probabilities[second_point] <= probabilities[i]
                    if first_monotonic_behavior == False:
                        is_monotone[first_index][second_index] = False
                        break

                elif is_monotonic_nondecreasing:
                    first_monotonic_behavior = probabilities[second_point] >= probabilities[i]
                    if first_monotonic_behavior == False:
                        is_monotone[first_index][second_index] = False
                        break

            second_index += 1
        first_index += 1
        second_index = 0

    plot = figure(plot_width=1000,
                  plot_height=1000,
                  x_range=(0, 1),
                  y_range=(0, 1),
                  x_axis_label='Process probability',
                  y_axis_label='Desired probability',
                  title='Monotonicity Plot (blue = monotone) [tolerance: ' + str(tolerance) + ']', tools='pan, wheel_zoom, reset, save',
                  active_drag='pan', active_scroll='wheel_zoom')

    plot.background_fill_color = 'beige'

    plot.border_fill_color = 'whitesmoke'
    plot.min_border = 60

    plot.title.text_font_size = '20pt'

    plot.xaxis.axis_label_text_font_size = '18pt'
    plot.xaxis.major_label_text_font_size = '16pt'

    plot.yaxis.axis_label_text_font_size = '18pt'
    plot.yaxis.major_label_text_font_size = '16pt'

    for i in range(max_val):
        process_prob = process_prob_list[i]
        monotone_probs = [process_prob_list[j] for j in range(max_val) if is_monotone[i][j]]
        non_monotone_probs = [process_prob_list[j] for j in range(max_val) if is_monotone[i][j] == False]

        plot.circle(x=[process_prob for x in range(len(monotone_probs))], y=monotone_probs, size=10,
                  color='blue')
        plot.circle(x=[process_prob for x in range(len(non_monotone_probs))], y=non_monotone_probs, size=10,
                  color='red')

    data = {'process_probability': [process_prob_list[i] for i in range(max_val) for j in range(max_val)],
        'desired_probability': [process_prob_list[i] for j in range(max_val) for i in range(max_val)]}

    data_cds = ColumnDataSource(data)

    tooltips = [
        ('p', '@process_probability'),
        ('q', '@desired_probability')
    ]

    hover_glyph = plot.circle(x='process_probability',
                              y='desired_probability',
                              source=data_cds,
                              size=15,
                              alpha=0,
                              hover_fill_color='green',
                              hover_alpha=1)

    plot.add_tools(HoverTool(tooltips=tooltips, renderers=[hover_glyph]))
    show(plot)


app = Flask(__name__)
Bootstrap(app)
nav = Nav(app)

@nav.navigation('nav_bar')
def create_navbar():
    home_view = View('Home', 'homepage')
    math_view = View('Math', 'mathpage')
    model_view = View('Model', 'modelpage')
    findings_view = View('Findings', 'findingspage')
    about_view = View('About', 'aboutpage')
    return Navbar('', home_view, math_view, model_view, findings_view, about_view)


@app.route('/')
def homepage():
    return render_template('index.html')


@app.route('/math')
def mathpage():
    return render_template('math.html')


@app.route('/model')
def modelpage():
    process_prob = request.args.get('process_probability')
    desired_numer = request.args.get("desired_numerator")
    desired_denom = request.args.get("desired_denominator")
    num_trials = request.args.get('number_of_trials')
    highlight = request.args.get('highlight')
    lines = request.args.get('lines')
    standardization = request.args.get('standardization')

    standardization = '' if standardization is None else str(standardization)

    if process_prob == None or desired_numer == None or desired_denom == None or num_trials == None:
        process_prob = 0.250
        desired_numer = 3
        desired_denom = 11
        num_trials = 147

    model = create_model(float(process_prob), int(desired_numer), int(desired_denom), int(num_trials), str(highlight), str(lines), standardization);
    script, div = components(model)
    return render_template('model.html', script=script, div=div, process_prob=process_prob, desired_numer=desired_numer, desired_denom=desired_denom, num_trials=num_trials)


@app.route('/findings')
def findingspage():
    return render_template('findings.html')


@app.route('/about')
def aboutpage():
    return render_template('about.html')


@app.route('/secret')
def secretpage():
    mono_model()


if __name__ == '__main__':
    app.run(port=5000, debug=True)
