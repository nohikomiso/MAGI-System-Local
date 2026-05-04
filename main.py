import os
import sys
import pkgutil

# Python 3.14+ compatibility bridge
if not hasattr(pkgutil, "find_loader"):
    from importlib.util import find_spec
    def find_loader(name):
        spec = find_spec(name)
        return spec.loader if spec else None
    pkgutil.find_loader = find_loader

from dash_extensions.enrich import Dash, Input, Output, State, Trigger, callback, ALL, MATCH
from dash import dcc
from dash.html import Div, Label, Span, Button
from dash_local_react_components import load_react_component
import ai

app = Dash(__name__)

Magi = load_react_component(app, 'components', 'magi.js')
WiseMan = load_react_component(app, 'components', 'wise_man.js')
Response = load_react_component(app, 'components', 'response.js')
Modal = load_react_component(app, 'components', 'modal.js')
Header = load_react_component(app, 'components', 'header.js')
Status = load_react_component(app, 'components', 'status.js')

app.layout = Div(
    className='system',
    children=[
        Magi(id='magi', children=[
            Header(side='left', title='質 問'),
            Header(side='right', title='解 決'),
            Status(id='status'),
            WiseMan(
                id={'type': 'wise-man', 'name': 'melchior'},
                name='melchior',
                order_number=1,
                personality='You are a scientist. Your goal is to further our understanding of the universe and advance our technological progress.'),
            WiseMan(
                id={'type': 'wise-man', 'name': 'balthasar'},
                name='balthasar',
                order_number=2,
                personality='You are a mother. Your goal is to protect your children and ensure their well-being.'),
            WiseMan(
                id={'type': 'wise-man', 'name': 'casper'},
                name='casper',
                order_number=3,
                personality='You are a woman. Your goal is to pursue love, dreams and desires.'),
            Response(id='response', status='info')
        ]),
        Div(className='input-section', children=[
            Div(className='input-header', children=[
                Span('SYSTEM COMMAND / QUERY ENTRY'),
                Button('最終審判を表示', id='reopen-verdict-btn', className='view-verdict-btn', style={'display': 'none'})
            ]),
            Div(className='input-container', children=[
                Label('QUESTION:'),
                dcc.Input(id='query', type='text', value='', debounce=True, autoComplete='off'),
            ]),
        ]),
        Modal(id={'type': 'modal', 'name': 'melchior'}, name='melchior'),
        Modal(id={'type': 'modal', 'name': 'balthasar'}, name='balthasar'),
        Modal(id={'type': 'modal', 'name': 'casper'}, name='casper'),

        dcc.Store(id='question', data={'id': 0, 'query': ''}),
        dcc.Store(id='annotated-question', data={'id': 0, 'query': '', 'is_yes_or_no_question': False}),
        dcc.Store(id='is_yes_or_no_question', data=False),
        dcc.Store(id='question-id', data=0),
        dcc.Store(id='consensus-trigger', data=None),

        # Consensus Visualizer Overlay
        Div(id='consensus-overlay', className='consensus-overlay', style={'display': 'none'}, children=[
            Div(id='verdict-text', className='verdict-text'),
            Div(id='consensus-summary', className='consensus-summary'),
            Div('クリックで閉じる', className='close-hint'),
        ]),
        
        # Syncing Indicator at root level
        Div('合議中', id='syncing-indicator', className='syncing-overlay'),
    ])


@callback(
    Output('question', 'data'),
    Input('query', 'value'),
    State('question', 'data'),
    prevent_initial_call=True)
def question(query: str, question: dict):
    return {'id': question['id'] + 1, 'query': query}


@callback(
    Output('annotated-question', 'data'),
    Input('question', 'data'),
    prevent_initial_call=True)
def annotated_question(question: dict):
    try:
        is_yes_or_no_question = ai.is_yes_or_no_question(question['query'])

        return {
            'id': question['id'],
            'query': question['query'],
            'is_yes_or_no_question': is_yes_or_no_question,
            'error': None
        }
    except Exception as e:
        return {
            'id': question['id'],
            'query': question['query'],
            'is_yes_or_no_question': False,
            'error': str(e)
        }


@callback(
    Output('status', 'extention'),
    Input('question', 'data'),
    Input('annotated-question', 'data'))
def extention(question: dict, annotated_question: dict):
    if question['id'] != annotated_question['id']:
        return '????'

    return '7312' if annotated_question['is_yes_or_no_question'] else '3023'


@callback(
    Output({'type': 'wise-man', 'name': MATCH}, 'answer'),
    Input('annotated-question', 'data'),
    State({'type': 'wise-man', 'name': MATCH}, 'personality'),
    State({'type': 'wise-man', 'name': MATCH}, 'name'),
    prevent_initial_call=True)
def wise_man_answer(question: dict, personality: str, name: str):
    if question['error']:
        return {'id': question['id'], 'name': name, 'response': question['error'], 'status': 'error'}

    try:
        answer = ai.get_answer(question['query'], personality)

        if question['is_yes_or_no_question']:
            classification = ai.classify_answer(question['query'], personality, answer)
        else:
            classification = {'status': 'info', 'conditions': None}

        return {
            'id': question['id'],
            'name': name,
            'response': answer,
            'status': classification['status'],
            'conditions': classification['conditions'],
            'error': None
        }

    except Exception as e:
        return {'id': question['id'], 'name': name, 'response': None, 'status': 'error', 'conditions': 'None', 'error': str(e)}


@callback(
    Output({'type': 'wise-man', 'name': MATCH}, 'question_id'),
    Input('question', 'data'))
def wise_man_question_id(question: dict):
    return question['id']


@callback(
    Output('response', 'question_id'),
    Input('question', 'data'))
def response_question_id(question: dict):
    return question['id']


@callback(
    Output('response', 'status'),
    Output('response', 'answer_id'),
    Output('syncing-indicator', 'className'),
    Output('consensus-trigger', 'data'),
    Input({'type': 'wise-man', 'name': ALL}, 'answer'),
    State('question', 'data'),
    prevent_initial_call=True)
def trigger_consensus(answers: list, question: dict):
    if not answers or any(a is None for a in answers) or question['id'] == 0:
        return 'info', 0, 'syncing-overlay', None

    if not all(answer.get('id') == question['id'] for answer in answers):
        return 'info', question['id'], 'syncing-overlay', None

    # Determine status for the background indicator
    status = 'info'
    if any([a['status'] == 'error' for a in answers]): status = 'error'
    elif any([a['status'] == 'no' for a in answers]): status = 'no'
    elif any([a['status'] == 'conditional' for a in answers]): status = 'conditional'
    elif all([a['status'] == 'yes' for a in answers]): status = 'yes'

    # Show "Syncing" indicator and trigger the next step
    return status, question['id'], 'syncing-overlay visible', {'id': question['id'], 'query': question['query'], 'status': status}


@callback(
    Output('consensus-overlay', 'style'),
    Output('consensus-overlay', 'className'),
    Output('verdict-text', 'children'),
    Output('consensus-summary', 'children'),
    Output('syncing-indicator', 'className', allow_duplicate=True),
    Output('reopen-verdict-btn', 'style'),
    Input('consensus-trigger', 'data'),
    State({'type': 'wise-man', 'name': ALL}, 'answer'),
    prevent_initial_call=True)
def generate_consensus(trigger_data, answers):
    if trigger_data is None:
        return {'display': 'none'}, 'consensus-overlay', '', '', 'syncing-overlay', {'display': 'none'}

    status = trigger_data['status']
    verdict_map = {
        'yes': '承認',
        'no': '拒絶',
        'conditional': '保留',
        'error': '異常'
    }
    verdict = verdict_map.get(status, '判定中')

    answer_dict = {
        'melchior': next((a['response'] for a in answers if a.get('name') == 'melchior'), '...'),
        'balthasar': next((a['response'] for a in answers if a.get('name') == 'balthasar'), '...'),
        'casper': next((a['response'] for a in answers if a.get('name') == 'casper'), '...')
    }

    summary = ai.summarize_consensus(trigger_data['query'], answer_dict)

    return {'display': 'flex'}, f'consensus-overlay {status}', verdict, summary, 'syncing-overlay', {'display': 'block'}


@callback(
    Output('consensus-overlay', 'style', allow_duplicate=True),
    Input('consensus-overlay', 'n_clicks'),
    prevent_initial_call=True)
def close_overlay(n):
    return {'display': 'none'}


@callback(
    Output('consensus-overlay', 'style', allow_duplicate=True),
    Input('reopen-verdict-btn', 'n_clicks'),
    prevent_initial_call=True)
def reopen_verdict(n):
    if n:
        return {'display': 'flex'}
    return {'display': 'none'}


@callback(
    Output({'type': 'modal', 'name': MATCH}, 'is_open'),
    Trigger({'type': 'wise-man', 'name': MATCH}, 'n_clicks'),
    prevent_initial_call=True)
def modal_visibility():
    return True


@callback(
    Output({'type': 'modal', 'name': MATCH}, 'question'),
    Output({'type': 'modal', 'name': MATCH}, 'answer'),
    Input('question', 'data'),
    Input({'type': 'wise-man', 'name': MATCH}, 'answer'))
def modal_content(question: dict, answer: dict):
    return question, answer


if __name__ == '__main__':
    app.run_server(debug=True)
