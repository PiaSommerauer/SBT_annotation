from utils import read_csv, to_csv
from utils import sort_by_key
from utils import read_group

from random import shuffle,sample
import os
import sys
import glob
from collections import Counter, defaultdict

def read_input(run, experiment_name):
    all_input_dicts = []
    input_dicts_batch = []
    f_paths_all = glob.glob(f'../prolific_input/run*-group_*/*.csv')
    f_paths_run_name = glob.glob(f'../prolific_input/run{run}-group_{experiment_name}/*.csv')
    header_path = f'../prolific_input/run{run}-group_{experiment_name}/header.txt'
    batch_numbers = []
    # Get info current batch
    if os.path.isfile(header_path):
        with open(header_path) as infile:
            header = infile.read().split(',')
        for f in f_paths_run_name:
            input_dicts = read_csv(f, header = header)
            input_dicts_batch.extend(input_dicts)
            if 'TEST' not in f:
                f_name = f.split('/')[-1]
                batch_n = int(f_name.split('-')[2].split('.')[0][len('batch'):])
                ##../prolific_input/run3-group_experiment1/qu70-s_qu70-batch11.csv
                batch_numbers.append(batch_n)
        # get all input dicts:
        for f in f_paths_all:
            run = f.replace('../prolific_input/', '').split('-')[0]
            #../prolific_input/run3-group_experiment1/qu70-s_qu70-batch11.csv
            input_dicts = read_csv(f, header = header)
            all_input_dicts.extend(input_dicts)
    return all_input_dicts, input_dicts_batch, batch_numbers


def collect_not_annotated(input_dicts, question_dicts):

    questions_not_annotated = []
    input_by_quid = sort_by_key(input_dicts, ['quid'])
    for d in question_dicts:
        quid = d['quid']
        if quid not in input_by_quid:
            questions_not_annotated.append(d)
    return questions_not_annotated


def get_annotated_questions(input_dicts, question_dicts):

    input_by_quid = sort_by_key(input_dicts, ['quid'])
    questions_by_quid = sort_by_key(question_dicts, ['quid'])
    questions_annotated = []
    for quid in input_by_quid:
        if quid in questions_by_quid:
            question = questions_by_quid[quid][0]
            questions_annotated.append(question)
    return questions_annotated


def collect_invalid(input_dicts, question_dicts):

    questions_by_pair = sort_by_key(question_dicts, ['property', 'concept'])
    questions_annotated = get_annotated_questions(input_dicts, question_dicts)
    questions_anntotated_by_pair = sort_by_key(questions_annotated, ['property', 'concept'])
    invalid_annotations = []

    for pair, questions_annotated in questions_anntotated_by_pair.items():
        questions = questions_by_pair[pair]
        if len(questions) != len(questions_annotated):
            #print('missing annotations for pair:', pair, len(questions), len(questions_annotated))
            invalid_annotations.extend(questions)
    return invalid_annotations

def get_available_questions(input_dicts, question_dicts):

    questions_for_annotation = []
    questions_not_annotated = collect_not_annotated(input_dicts, question_dicts)
    print('not annotated yet:', len(questions_not_annotated))
    invalid_annotations = collect_invalid(input_dicts, question_dicts)
    print('not valid', len(invalid_annotations))

    not_annotated_pair = sort_by_key(questions_not_annotated, ['property', 'concept'])
    invalid_pair = sort_by_key(invalid_annotations, ['property', 'concept'])

    for pair, questions in not_annotated_pair.items():
        if pair in invalid_pair:
            questions_for_annotation.extend(invalid_pair[pair])
        else:
            questions_for_annotation.extend(questions)
    test_for_wrong_questions(questions_for_annotation)
    return questions_for_annotation, invalid_annotations

def test_for_wrong_questions(questions_for_annotation):
    wrong_n_questions = []
    for_annotation_by_pair = sort_by_key(questions_for_annotation, ['property', 'concept'])
    for pair, questions in for_annotation_by_pair.items():
        if len(questions) > 10 or len(questions) < 3:
            print(pair, len(questions))
            for d in questions:
                print(d['relation'])
            print()
            wrong_n_questions.append((len(questions), pair))
    assert len(wrong_n_questions) == 0, 'Number of questions per pair not correct.'





def get_batch(questions_to_annotate, n_qu = 70):
    batch = []
    properties = set()
    pairs = set()
    # shuffle questions:
    shuffle(questions_to_annotate)
    questions_by_pair = sort_by_key(questions_to_annotate, ['property', 'concept'])
    available_properties = set([p.split('-')[0] for p in questions_by_pair.keys()])
    print('total number of questions to select:', n_qu)
    print('available properties', available_properties)
    print('# available questions', len(questions_to_annotate))
    if n_qu > len(questions_to_annotate):
        print(f'only {len(questions_to_annotate)} left - adding all to batch.')
        batch.extend(questions_to_annotate)
    else:
        print(f'still more than {n_qu} questions available.')

        while len(batch) < n_qu:
            for pair, questions in questions_by_pair.items():
                prop = pair.split('-')[0]
                if len(batch) < n_qu:
                    if prop not in properties:
                        print('found a new property:', prop, len(batch))
                        batch.extend(questions)
                        properties.add(prop)
                        pairs.add(pair)
                    else:
                        print('no more new properties')
                        props_not_used = available_properties.difference(properties)
                        print('properties not used:', len(props_not_used), len(batch))
                        if len(props_not_used) > 0:
                            continue
                        else:
                            if pair not in pairs:
                                batch.extend(questions)
                                properties.add(prop)
                                print('no more properties, adding quetions:', len(questions))
                            else:
                                print('pair already added', pair)
                else:
                    print('found enough questions', len(batch))
                    break

    return batch


def batch_to_file(batch, url, experiment_name, run, n_qu, n_lists, batch_n):

    # header = ['quid', 'question', 'example_pos', 'example_neg']
    header_new = ['quid','listNr', 'description', 'exampleTrue', 'exampleFalse',\
                  'triple', 'completionUrl', 'name']
    dirpath = f'../prolific_input/run{run}-group_{experiment_name}/'
    batch_name = f'qu{n_qu}-s_qu{n_lists}-batch{batch_n}'
    filepath = f'{dirpath}{batch_name}.csv'
    pl_name = f'Agree or disagree (run{run}-{experiment_name}-batch{batch_n}-{n_qu}-{n_qu})'

    ### write header###
    if not os.path.isdir(dirpath):
        os.mkdir(dirpath)
    header_path = f'{dirpath}header.txt'
    if not os.path.isfile(header_path):
        with open(header_path, 'w') as outfile:
            outfile.write(','.join(header_new))
    ###
    new_dicts = []
    for d in batch:
        triple = f"{d['relation']}-{d['property']}-{d['concept']}"
        new_d = dict()
        new_d['quid'] = d['quid']
        new_d['listNr'] = d['listNr']
        new_d['description'] = d['question']
        new_d['exampleTrue'] = d['example_pos']
        new_d['exampleFalse'] = d['example_neg']
        new_d['run'] = run
        new_d['subList'] = 1
        new_d['completionUrl'] = url
        new_d['triple'] = triple
        new_d['name'] = pl_name
        new_dicts.append(new_d)
    to_csv(filepath, new_dicts, header=True)
    return filepath


def test_duplicates(input_dicts, batch_dicts, invalid_annotations):

    quids_batch = set([d['quid'] for d in batch_dicts])
    quids_input = set([d['quid'] for d in input_dicts])
    quids_invalid = set([d['quid'] for d in invalid_annotations])
    overlap = quids_batch.intersection(quids_input)
    valid_overlap = overlap.difference(quids_invalid)
    #print(f'Overlap between annotated and current batch: {len(valid_overlap)}')
    #print(valid_overlap)
    problematic_overlap = []
    for quid in valid_overlap:
        if quid.startswith('test') or quid.startswith('check'):
            continue
        else:
            problematic_overlap.append(quid)
    assert len(problematic_overlap) == 0, 'Already annotated questions in batch!'

def suggest_cost(n_questions):
    # UK min wage = 8.21
    # divided by 60 gives min wage per minute
    per_minute = 0.13
    time_per_question_seconds = 7
    price_per_question = (per_minute/60) *time_per_question_seconds
    final = n_questions * price_per_question
    estimated_time = (n_questions * time_per_question_seconds) / 60
    print(f'estimated time: {estimated_time} minutes')
    print(f'suggested price: {final}')
    return final, estimated_time


def print_task_intro(run):

    # load description:

    with open(f'../task_set_up/description_run{run}.txt') as infile:
        text_description = infile.read()

    with open(f'../task_set_up/instructions_run{run}.txt') as infile:
        text_instructions = infile.read()

    print('-------------------------------------\n')
    print_des = input('Print description? (y/n)')
    if print_des == 'y':
        print('\n----- Task description ------\n')
        print(text_description)
    print_instructions = input('Print instructions? (y/n)')
    if print_instructions == 'y':
        print('\n----- Instructions ------\n')
        print(text_instructions)
    print_whitelist = input("Print whitelist (y/n)?")
    if print_whitelist == 'y':
        with open('../task_set_up/whitelist.txt') as infile:
            whitelist = infile.read()
        print('------- Whitelist--------')
        print(whitelist)
    return print_whitelist


def update_log(new_log_dict):
    path = '../task_set_up/experiment_log.csv'
    log_dicts = read_csv(path)
    log_dicts.append(new_log_dict)
    to_csv(path, log_dicts)
    print(f'updated log: {path}')


def get_questions(run, experiment_name, all_input_dicts, input_dicts_batch):

    question_path = f'../questions/run{run}-all-restricted_True.csv'
    question_dicts = read_csv(question_path)
    selected_properties = read_group(experiment_name)
    print('all input dicts, input dicts batch:', len(all_input_dicts), len(input_dicts_batch))

    print('available for batch:')
    questions_to_annotate_batch, invalid_annotations = get_available_questions(input_dicts_batch,
                                                                               question_dicts)
    print('availabel in total:')
    questions_to_annotate_total, invalid_annotations = get_available_questions(all_input_dicts,
                                                                               question_dicts)
    questions_in_selection = [d for d in questions_to_annotate_batch
                              if d['property'] in selected_properties]
    questions_in_selection_total = [d for d in question_dicts
                                    if d['property'] in selected_properties]

    ### Get counts ###
    # Total dataset
    n_total = len(question_dicts)
    n_not_annotated = len(questions_to_annotate_total)
    n_annotated = n_total - n_not_annotated
    percent_total = round(n_annotated / n_total, 3) * 100
    ###

    # Experiment group
    n_experiment_group = len(questions_in_selection_total)
    n_not_annotated_experiment_group = len(questions_in_selection)
    n_annotated_experiment_group = n_experiment_group - n_not_annotated_experiment_group
    percent_experiment_group = round(n_annotated_experiment_group / n_experiment_group, 3) * 100
    ###
    ###########
    print(f'Percentage of annotated questions of {experiment_name}: {percent_experiment_group}%')
    print(f'Number of questions in the total dataset: {n_total}')
    print(f'Number of questions in {experiment_name}: {n_experiment_group}')
    print(f'Number of annotated questions: {n_annotated}\
        (of which in {experiment_name}: {n_annotated_experiment_group})')
    print(f'Percentage of annotated questions of the total: {percent_total}%')
    print(f'Percentage of annotated questions of {experiment_name}: {percent_experiment_group}%')

    return questions_in_selection


def distribute_over_lists(new_batch, n_qu, n_lists, test_question_dicts):
    batch_with_listnumbers = []

    new_batch_by_pair = sort_by_key(new_batch, ['property', 'concept'])
    pair_by_n = defaultdict(list)
    for p, data in new_batch_by_pair.items():
        pair_by_n[len(data)].append(p)

    pairs_assigned = set()
    batch_dict = defaultdict(list)
    for n, pairs in pair_by_n.items():
        for list_n in range(n_lists):
            list_n = list_n + 1
            for p in pairs:
                if p not in pairs_assigned:
                    questions = new_batch_by_pair[p]
                    batch_dict[list_n].extend(questions)
                    pairs_assigned.add(p)
                    if len(batch_dict[list_n]) >= (n_qu-10):
                        break
    return batch_dict


def add_tests(batch_dict, test_question_dicts):
    for list_n, questions in batch_dict.items():
        tests_drawn = sample(test_question_dicts, k=2)
        tests_new = []
        # make new dicts for tests:
        for t in tests_drawn:
            new_d = dict()
            new_d.update(t)
            tests_new.append(new_d)
        print('# tests for list #', list_n, ':')
        print(len(tests_new))
        questions.extend(tests_new)


def create_new_batch(run, experiment_name, url, n_participants, n_lists, n_qu=70, test=False):
    exp_dict = dict()

    all_input_dicts, input_dicts_batch, batch_numbers = read_input(run, experiment_name)

    questions_in_selection = get_questions(run, experiment_name, all_input_dicts, input_dicts_batch)
    test_question_path = f'../questions/run{run}-TEST.csv'
    test_question_dicts = read_csv(test_question_path)

    # Create new batch
    if batch_numbers:
        highest_batch_number = max(batch_numbers)
    else:
        highest_batch_number = 0
    if test == False:
        current_batch_n = highest_batch_number + 1
    else:
        current_batch_n = 'TEST'

    # collect all questions in one go:
    n_qu_total = n_qu * n_lists
    new_batch = get_batch(questions_in_selection, n_qu=n_qu_total)
    batch_dict = distribute_over_lists(new_batch, n_qu, n_lists, test_question_dicts)
    add_tests(batch_dict, test_question_dicts)

    # create list with all sublists and add listn to dicts:
    batch_with_listnumbers = []
    for listn, questions in batch_dict.items():
        for d in questions:
            d['listNr'] = listn
            print(listn, len(questions))
            batch_with_listnumbers.append(d)

    # check for duplicate questions:
    quids = [d['quid'] for d in batch_with_listnumbers]
    quid_counter = Counter(quids)
    test_for_duplicates_within_batch= 'ok'
    for quid, cnt in quid_counter.most_common():
        if cnt >1 and not quid.startswith('test'):
            test_for_duplicates_within_batch = 'problem'
            print('Problematic quesiton:', quid)
            break
    assert test_for_duplicates_within_batch == 'ok', 'Found question duplicates'
    # Write batch to file
    batch_path = batch_to_file(batch_with_listnumbers, url, experiment_name, run, n_qu, n_lists, current_batch_n)

    print(f'Annotated {highest_batch_number} batches so far.')
    print(f'Created batch {current_batch_n} with {len(batch_with_listnumbers)} questions.')
    print(f'New batch written to: {batch_path}')
    pl_n = f'Agree or disagree (run{run}-{experiment_name}-batch{current_batch_n}-{n_qu}-{n_lists})'
    print(pl_n)
    p_whitelist = print_task_intro(run)

    # suggest cost
    print('\n------ Cost ---------')
    n_questions_average = len(batch_with_listnumbers)/n_lists
    n_participants_total = n_participants * n_lists
    print(f'\nCost suggestion for {n_questions_average} questions:\n')
    sug_cost, t = suggest_cost(n_questions_average)

    total_cost_no_fee = sug_cost * n_participants_total
    # fill log dict:
    exp_dict['name_lingoturk'] = pl_n
    exp_dict['name_prolific'] = pl_n
    exp_dict['group'] = experiment_name
    exp_dict['batch'] = current_batch_n
    exp_dict['run'] = run
    exp_dict['n_questions'] = n_qu
    exp_dict['n_questions_batch'] = len(batch_with_listnumbers)
    exp_dict['n_lists'] = n_lists
    exp_dict['n_participants'] = n_participants
    exp_dict['minutes_planned'] = t
    exp_dict['reward (pounds)'] = sug_cost
    total_cost = float(input('Enter total cost shown on Prolific: '))
    exp_dict['total_cost (pounds)'] =  total_cost
    print(f'Prolific charges {float(total_cost) - total_cost_no_fee} pounds fees.')
    exp_dict['posted'] = 'yes'
    exp_dict['results_downloaded'] = ''
    exp_dict['summary downloaded'] = ''
    exp_dict['approved'] = ''
    exp_dict['comment'] = ''
    exp_dict['Code'] = url
    exp_dict['whitelist'] = p_whitelist
    if test == False:
        update_log(exp_dict)


def main():
    run = sys.argv[1]
    experiment_name = 'experiment_scalar'
    url = sys.argv[2]
    # number of lists within batch
    n_lists = int(sys.argv[3])
    n_participants_per_question = int(sys.argv[4])
    n_qu = 70

    if url == 'TEST':
        test = True
        url = 'https://piasommerauer.github.io/annotation'
    elif url != 'TEST':
        test = False

    create_new_batch(run, experiment_name, url, n_participants_per_question, n_lists, n_qu=n_qu, test=test)


if __name__ == '__main__':
    main()
