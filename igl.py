from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from flask_nav.elements import Navbar, Subgroup, View
from flask_nav import Nav
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource
from bokeh.models import HoverTool
from bokeh.models import Legend
import math


def factorial(num):
    f = 1
    while num > 0:
        f *= num
        num -= 1
    return f


def permutation(n, k):
    if k > n or n < 0 or k < 0:
        raise ValueError
    return factorial(n) / factorial(n - k)


def combination(n, k):
    return permutation(n, k) / factorial(k)


def bernoulli_trial(success_probability, desired_successes, num_trials):
    if success_probability < 0 or success_probability > 1 or desired_successes < 0 or desired_successes > num_trials:
        raise ValueError
    failure_probability = 1 - success_probability
    desired_failures = num_trials - desired_successes
    return combination(num_trials, desired_successes) * (success_probability ** desired_successes) * (
            failure_probability ** desired_failures)


def bernoulli_trial_sum(success_probability, min_successes, num_trials):
    probability_sum = 0
    desired_successes = min_successes
    while desired_successes <= num_trials:
        probability_sum += bernoulli_trial(success_probability, desired_successes, num_trials)
        desired_successes += 1
    return probability_sum


def compute_model(process_prob, min_success_rate, num_trials):
    try:
        current_trial_count = 1
        results = []
        while current_trial_count <= num_trials:
            min_successes = math.ceil(min_success_rate * current_trial_count)
            long_term_prob = bernoulli_trial_sum(process_prob, min_successes, current_trial_count)
            results.append(long_term_prob)
            current_trial_count += 1
        return results
    except ValueError:
        return [0 for x in range(num_trials)]


def create_model(process_prob, desired_prob, num_trials):
    data = {'trial_count': [x + 1 for x in range(num_trials)],
            'probability': compute_model(process_prob, desired_prob, num_trials)}

    data_cds = ColumnDataSource(data)

    title = 'Probability Model'

    model = figure(plot_width=900,
                  plot_height=900,
                  x_range=(0, num_trials + 3),
                  y_range=(0, 1.03),
                  x_axis_label='Trial count',
                  y_axis_label='Probability to achieve desired success',
                  title=title, tools='pan, wheel_zoom, reset, save',
                  active_drag='pan', active_scroll='wheel_zoom')

    model.background_fill_color = 'beige'

    model.border_fill_color = 'whitesmoke'
    model.min_border = 60

    model.title.text_font_size = '20pt'

    model.xaxis.axis_label_text_font_size = '18pt'
    model.xaxis.major_label_text_font_size = '16pt'

    model.yaxis.axis_label_text_font_size = '18pt'
    model.yaxis.major_label_text_font_size = '16pt'

    model.circle(x='trial_count',
                y='probability',
                source=data_cds,
                size=10,
                color='blue')

    tooltips = [
        ('Trial count', '@trial_count'),
        ('Probability', '@probability'),
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

app = Flask(__name__)
Bootstrap(app)
nav = Nav(app)

@nav.navigation('nav_bar')
def create_navbar():
    home_view = View('Home', 'homepage')
    model_view = View('Model', 'modelpage')
    findings_view = View('Findings', 'findingspage')
    about_view = View('About', 'aboutpage')
    return Navbar('', home_view, model_view, findings_view, about_view)


@app.route('/')
def homepage():
    return render_template('index.html')


@app.route('/model')
def modelpage():
    process_prob = request.args.get('process_probability')
    desired_numer = request.args.get("desired_numerator")
    desired_denom = request.args.get("desired_denominator")
    num_trials = request.args.get('number_of_trials')

    if process_prob == None or desired_numer == None or desired_denom == None or num_trials == None:
        process_prob = 0.5
        desired_numer = 1
        desired_denom = 2
        num_trials = 100
        
    model = create_model(float(process_prob), float(desired_numer) / float(desired_denom), int(num_trials));
    script, div = components(model)
    return render_template('model.html', script=script, div=div, process_prob=process_prob, desired_numer=desired_numer, desired_denom=desired_denom, num_trials=num_trials)


@app.route('/findings')
def findingspage():
    return render_template('findings.html')


@app.route('/about')
def aboutpage():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(port=5000, debug=True)
