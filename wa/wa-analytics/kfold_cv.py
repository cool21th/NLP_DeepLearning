# -*- coding: utf-8 -*-

# Copyright 2015 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: Thiago Salles [tsalles@br.ibm.com]

import sys
import csv
import json
import random
import os
import time
import math

from argparse import ArgumentParser
from datetime import datetime
from threading import Thread
from watson_developer_cloud import ConversationV1


class ArgParser(ArgumentParser):
    """
    Parses the arguments send to the module when called from command line.
    """
    def error(self, message):
        sys.stderr.write('Error when parsing arguments: %s\n' % message)
        self.print_help()
        sys.exit('Process terminated with errors when parsing arguments.')


class ConversationManager:
    """Handles operations regarding IBM Watson Conversation's workspaces.

    Attributes:
        - workspace_id: The ID of the workspace to be used
        - username: The username from the Conversation service credentials
        - password: The password from the Conversation service credentials
    """

    CONVERSATION_VERSION = '2017-05-26'

    def __init__(self, username, password):
        self.username = username
        self.password = password

        self.conversation = ConversationV1(username=username, password=password, url='https://gateway.aibril-watson.kr/conversation/api', version=self.CONVERSATION_VERSION)#, x_watson_learning_opt_out=True)
        self.conversation.x_watson_learning_opt_out = True

    def download_workspace_file(self, workspace_id):
        """
        Downloads the workspace JSON file containing all of the workspace data.
        :param workspace_id: The ID of the workspace to download.
        :return: The workspace JSON file.
        """

        try:
            response = self.conversation.get_workspace(workspace_id=workspace_id, export=True)
        except Exception as e:
            print('Error: {}'.format(e))
            sys.exit(str(e))

        return response

    def create_workspace(self, workspace_json):
        """
        Creates a workspace from a given JSON file
        :param workspace_json: The JSON file to create the workspace from.
        :return: The created workspace ID.
        """
        try:
            response = self.conversation.create_workspace(name=workspace_json['name'],
                                                          description=workspace_json['description'],
                                                          language=workspace_json['language'],
                                                          intents=workspace_json['intents'],
                                                          entities=workspace_json['entities'],
                                                          dialog_nodes=workspace_json['dialog_nodes'],
                                                          counterexamples=workspace_json['counterexamples'],
                                                          learning_opt_out=True)
        except Exception as e:
            print('Error: {}'.format(e))
            sys.exit(str(e))

        return response['workspace_id']

    def send_message(self, message, workspace_id):
        """
        Sends a message to the Conversation service.
        :param message: The message to be sent.
        :param workspace_id: The ID of the workspace that will receive the message.
        :return: The default web service response, a JSON with a list of entities and intents.
        """
        for retry in range(1, 11):
            try:
                response = self.conversation.message(workspace_id=workspace_id, input={'text': message},
                                                     alternate_intents=True, )
                break
            except Exception as e:
                print('Error on Retry {}: {}. Trying again!'.format(retry, e))
                if retry == 10:
                    print('Abording experiment now.')
                    sys.exit(str(e))
                time.sleep(0.5)
        return response

    def is_workspace_trained(self, workspace_id):
        """
        Checks if a workspace with the given workspace ID is trained or not
        :param workspace_id: The workspace ID to check the training status
        :return: True if the workspace is trained, False otherwise
        """
        try:
            response = self.conversation.get_workspace(workspace_id=workspace_id)
            status = response['status']
        except Exception as e:
            print('Error: {}'.format(e))
            sys.exit(str(e))

        return status == 'Available'

    def delete_workspace(self, workspace_id):
        """
        Deletes the workspace with the given workspace ID
        :param workspace_id: The ID of the workspace to delete
        """
        try:
            self.conversation.delete_workspace(workspace_id)
        except Exception as e:
            print('Error: {}'.format(e))
            sys.exit(str(e))


class DataPreparer:
    """
    Contains a set of operations that manipulate the data extracted from the Conversation file.
    """

    @staticmethod
    def denormalize_examples_and_intents(workspace_json, no_whitespaces=False):
        """
        Creates a list of examples and their expected intent from the conversation workspace JSON.
        :param workspace_json: The workspace JSON file from which to extract the data.
        :return: A list of input - output examples.
        """
        example_intent_list = []
        for intent in workspace_json['intents']:
            for example in intent['examples']:
                txt = example['text'] if not no_whitespaces else "".join(example['text'].split())
                example_intent_list.append({'input': txt, 'output': intent['intent']})

        random.shuffle(example_intent_list)

        return example_intent_list

    @staticmethod
    def divide_data_in_k_folds(denormalized_data, number_of_folds):
        """
        Divides the denormalized data in the specified number of folds and returns it in a dictionary
        where the key is the fold number and the value is a list of examples for that fold.
        :param denormalized_data: The denormalized data which should be a list of input - output examples.
        :param number_of_folds: The number of folds to separate the data into.
        :return: A dicionary with data divided by fold number.
        """
        folds = {index: [] for index in range(number_of_folds)}

        for index, denormalized_example in enumerate(denormalized_data):
            fold_index = index % number_of_folds
            folds[fold_index].append(denormalized_example)

        return folds

    @staticmethod
    def get_test_and_train_sets_for_fold(data_folds, fold_number, no_whitespaces=False):
        """
        Creates a tuple of test and train data for a given fold number from the folded data
        :param data_folds: The folded data to be used when generating the tuple
        :param fold_number: The number of the folder to which the data will be generated
        :return: A tuple of test and train data sets for the given fold number
        """
        test_data = []
        for example in data_folds[fold_number]:
            txt = example['input'] if not no_whitespaces else "".join(example['input'].split())
            test_data.append({'input': txt, 'output': example['output']})

        unique_train_data = {}
        for index, data in enumerate(data_folds):
            if index != fold_number:
                for example in data_folds[index]:
                    txt = example['input'] if not no_whitespaces else "".join(example['input'].split())
                    unique_train_data[txt] = {'input': txt, 'output': example['output']}

        return test_data, list(unique_train_data.values())


    @staticmethod
    def normalize_data_from_train_set(train_set):
        """
        Creates a dictionary of intents by their examples from a denormalized train set
        :param train_set: The denormalized train set to normalize
        :return: A dictionary of intents by their examples
        """
        intents = {}
        for example in train_set:
            current_intent = example['output']

            if current_intent not in intents:
                intents[current_intent] = []

            intents[current_intent].append(example['input'])

        return intents

    @staticmethod
    def create_workspace_for_fold(train_set, fold_number, entities, counterexamples, language):
        """
        Creates a conversation workspace file from a training set.
        :param train_set: A denormalized list of input - output examples.
        :param fold_number: The number of the fold to which the workspace will be created for.
        :param entities: The entities part of the workspace JSON.
        :return: A workspace JSON file.
        """
        workspace_name = 'k-fold cross-validation - {}'.format(fold_number)

        workspace = {
            'dialog_nodes': [],
            'entities': entities,
            'language': language,
            'intents': [],
            'counterexamples': counterexamples,
            'name': workspace_name,
            'created': str(datetime.now()),
            'description': workspace_name,
            'learning_opt_out': True
        }

        normalized_data = DataPreparer.normalize_data_from_train_set(train_set)

        for intent, examples in normalized_data.items():
            entry = {'intent': intent, 'examples': []}

            for example in examples:
                entry['examples'].append({'text': example, 'created': str(datetime.now())})

            workspace['intents'].append(entry)

        return workspace


class ExperimentRunner:
    """
    Orchestrates and runs the experiment against an instance of IBM Watson Conversation.
    Starts as many threads as the number of k folds in the experiment
    """

    def __init__(self, conversation_manager, results_folder, number_of_folds, workspace_id, folds_dir=None, no_entities=False, no_whitespaces=False, language=None):
        self.conversation_manager = conversation_manager
        self.results_folder = results_folder
        self.number_of_folds = number_of_folds
        self.workspace_id = workspace_id
        self.folds_dir = folds_dir if folds_dir else ''
        self.no_entities = no_entities
        self.no_whitespaces = no_whitespaces
        self.language = language

    def run_experiment(self):
        """
        Runs the entire the experiment by creating a thread for each fold that has to be tested.
        """
        dataset_by_class = self.prepare_data()

        threads = []

        for fold_number in range(self.number_of_folds):
            thread = Thread(name='Crossfold validation {}'.format(fold_number), target=self.execute_experiment,
                            args=(fold_number,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        print('Generating the reports for the experiment')
        self.generate_reports(dataset_by_class)
        print('Reports generated on {}'.format(results_folder))

    def prepare_data(self):
        """
        Prepares the data by denormalizing it, dividing into k folds, separating test and train set for
        each of the folds and writing it to the specified output directory.
        """
        if not os.path.exists(self.results_folder):
            os.makedirs(self.results_folder)

        downloaded_workspace = conversation_manager.download_workspace_file(self.workspace_id)

        denormalized_intents_and_examples = DataPreparer.denormalize_examples_and_intents(downloaded_workspace, self.no_whitespaces)
        dataset_by_class = {}
        with open(self.get_dataset_file_name(), 'w', newline="\n", encoding="UTF-8") as dataset_file:
            dataset_writer = csv.writer(dataset_file)
            for example in denormalized_intents_and_examples:
                dataset_writer.writerow([example['input'], example['output']])
                if example['output'] not in dataset_by_class:
                    dataset_by_class[example['output']] = [example['input']]
                else:
                    dataset_by_class[example['output']].append(example['input'])

        print('Data set size: {}'.format(len(denormalized_intents_and_examples)))

        if self.check_previous_folds():
            print('Loading previous folds at {}'.format(self.folds_dir))
            data_folds = self.load_previous_folds()
        else:
            data_folds = DataPreparer.divide_data_in_k_folds(denormalized_intents_and_examples, self.number_of_folds)
        for index in data_folds:
            with open(self.get_folder_name(index), 'w', newline="\n", encoding="UTF-8") as folder_file:
                folder_writer = csv.writer(folder_file)
                for r in data_folds[index]:
                    folder_writer.writerow([r['input'], r['output']])

        for fold_number in range(self.number_of_folds):
            test_set, train_set = DataPreparer.get_test_and_train_sets_for_fold(data_folds, fold_number, self.no_whitespaces)
            print('Fold {} | Train set: {} | Test set: {}'.format(fold_number, len(train_set), len(test_set)))

            workspace = DataPreparer.create_workspace_for_fold(train_set, fold_number,
                                                               downloaded_workspace['entities'] if not self.no_entities else [],
                                                               downloaded_workspace['counterexamples'],
                                                               downloaded_workspace['language'] if not self.language else self.language)

            with open(self.get_train_workspace_name(fold_number), 'w', newline="\n", encoding="UTF-8") as train_file, \
                    open(self.get_test_file_name(fold_number), 'w', newline="\n", encoding="UTF-8") as test_file:

                json.dump(workspace, train_file, ensure_ascii=False)

                test_writer = csv.writer(test_file)

                for example in test_set:
                    test_writer.writerow([example['input'], example['output']])
        return dataset_by_class

    def check_previous_folds(self):
        for i in range(self.number_of_folds):
            if not os.path.isfile(self.get_folder_name(i, self.folds_dir)):
                return False
        return True

    def load_previous_folds(self):
        folds = {index: [] for index in range(self.number_of_folds)}
        for i in range(self.number_of_folds):
            with open(self.get_folder_name(i, self.folds_dir), encoding="UTF-8") as folder_file:
                folder_reader = csv.reader(folder_file)
                folds[i] = [{'input': r[0], 'output': r[1]} for r in folder_reader]
        return folds

    def execute_experiment(self, fold_number):
        """
        Executes the experiment for the given fold number.
        :param fold_number: The fold number.
        """
        created_workspace_id = self.initialize_workspace(fold_number)

        self.execute_cross_validation(fold_number, created_workspace_id)

        print('Deleting temporary workspace {} - {}'.format(fold_number, created_workspace_id))
        self.delete_crossfold_workspace(created_workspace_id)

    def initialize_workspace(self, fold_number):
        """
        Creates and trains the crossfold validation workspace for the given fold number.
        :param fold_number: The number of the fold that will own the workspace.
        :return: The newly created workspace ID.
        """
        with open(self.get_train_workspace_name(fold_number), 'r', encoding="UTF-8") as workspace_file:
            workspace_json = json.load(workspace_file)

        print('Creating workspace {}'.format(fold_number))
        new_workspace_id = ''
        try:
            new_workspace_id = conversation_manager.create_workspace(workspace_json)
            print('Workspace: {}'.format(new_workspace_id))
        except Exception as e:
            print('ERROR: {}'.format(e))
            sys.exit(str(e))

        trained = False
        query_count = 0
        max_queries = 30  # Assures that we keep trying for 5 minutes max
        seconds_to_sleep = 10

        while not trained:
            trained = conversation_manager.is_workspace_trained(new_workspace_id)
            query_count += 1

            if not trained:
                if query_count == max_queries:
                    sys.exit('Training workspace {} has timed out. Process exiting...'.format(fold_number))

                time.sleep(seconds_to_sleep)
            else:
                print('Workspace {} trained.'.format(fold_number))

        return new_workspace_id

    def execute_cross_validation(self, fold_number, workspace_id):
        """
        Executes the cross validation test by sending messages with unseen data to the trained model.
        Saves the predicted intents in a text file on the output directory.
        :param fold_number: The number of the fold to execute the validation for.
        :param workspace_id: The ID of the workspace that will receive the messages.
        """
        print('Evaluating fold {} with workspace ID {}'.format(fold_number, workspace_id))

        hits = 0
        total = 0

        with open('{}/predictions_{}.txt'.format(self.results_folder, fold_number), 'w', encoding="UTF-8") as predictions:
            for inpt, expected_intent in self.read_test_file_lines(fold_number):
                response = conversation_manager.send_message(inpt, workspace_id)

                predicted_intents = response['intents']
                top_scoring_intent = predicted_intents[0]['intent']

                if top_scoring_intent == expected_intent:
                    hits += 1

                total += 1

                if total % 50 == 0:
                    print('Fold {}: Processed {}. Accuracy: {}'.format(fold_number, total, hits / total))

                predictions.write('{} {} '.format(total, expected_intent) + ' '.join(
                    ['{}:{}'.format(prediction['intent'], prediction['confidence']) for prediction in predicted_intents])
                                  + '\n')

    def delete_crossfold_workspace(self, workspace_id):
        """
        Deletes the workspace with the specified ID.
        :param workspace_id: The ID of the workspace to be deleted.
        """
        conversation_manager.delete_workspace(workspace_id)

    def generate_reports(self, dataset_by_class):
        """
        Generates reports on the results of the experiment for the specified fold number.
        :param dataset_by_class: A dictionary with the examples grouped by classes
        """
        ReportGenerator(self.results_folder).generate_reports(self.number_of_folds, dataset_by_class)

    def read_test_file_lines(self, fold_number):
        """
        Reads the test file for the kth fold and returns a generator which returns a tuple for each line.
        The tuple consists of the input text and the expected intent.
        :param fold_number: The number of the fold to read the test file
        :return: A tuple of input text and expected intent, which is a line on the test file.
        """
        with open(self.get_test_file_name(fold_number), 'r', encoding="UTF-8") as test_file:
            test_reader = csv.reader(test_file, delimiter=',')
            for row in test_reader:
                yield row[0], row[1]

    def get_train_workspace_name(self, fold_number):
        """
        Gets the train workspace JSON file name according to the fold number.
        :param fold_number: The number of the fold that owns the workspace.
        :return: A string representing the name of the workspace file, including its directory.
        """
        return '{}/{}{}.json'.format(self.results_folder, 'train_workspace_', fold_number)

    def get_dataset_file_name(self):
        """
        Gets the dataset CSV file name.
        :return A string representing the name of the dataset file, in CSV format.
        """
        return '{}/{}.csv'.format(self.results_folder, 'dataset')

    def get_folder_name(self, fold_number, prev_dir=None):
        """
        Gets the fold CSV file name according to the fold number.
        :param fold_number: The number of the fold that owns the data.
        :return: A string representing the name of the fold file, including its directory.
        """
        return '{}/{}{}.csv'.format(self.results_folder if not prev_dir else prev_dir, 'fold_', fold_number)

    def get_test_file_name(self, fold_number):
        """
        Gets the test CSV file name according to the fold number.
        :param fold_number: The number of the fold that owns the test data.
        :return: A string representing the name of the test file, including its directory.
        """
        return '{}/{}{}.csv'.format(self.results_folder, 'test_', fold_number)


class ReportGenerator:
    """
    Generates reports from the results of the experiment
    """

    def __init__(self, results_folder):
        self.results_folder = results_folder

    def generate_reports(self, number_of_folds, dataset_by_class):
        """
        Generates the reports for the experiment results.
        :param number_of_folds: The number of folds used on the experiment.
        :param dataset_by_class: training data grouped by classes.
        """
        if not os.path.exists(self.get_pairwise_analysis_dir_name()):
            os.makedirs(self.get_pairwise_analysis_dir_name())

        precisions_at_k = []
        confusion_matrix = {}
        confidence_matrix = {}

        for fold_number in range(number_of_folds):
            hits_at_k = {}
            total = 0

            with open(self.get_predictions_file_name(fold_number), 'r', encoding="UTF-8") as predictions_file:
                for line in predictions_file:
                    total += 1
                    line_fields = self.get_predictions_line_fields(line)
                    expected_intent = self.get_expected_intent(line_fields)

                    prediction_found = False

                    for index, prediction_and_confidence in enumerate(self.get_other_predictions_from_line(line_fields)):
                        prediction, confidence = prediction_and_confidence.split(':')
                        confidence = float(confidence)

                        prediction_found = prediction_found or expected_intent == prediction

                        if prediction_found:
                            hits_at_k[index] = hits_at_k.get(index, 0) + 1

                        if index == 0:
                            self.add_prediction_to_matrices(expected_intent, prediction, confidence,
                                                            confusion_matrix, confidence_matrix)

            precisions_at_k.append({k: hit_count / total for k, hit_count in hits_at_k.items()})

        self.write_precision_at_k_file(precisions_at_k)
        self.write_pairwise_file(confidence_matrix, confusion_matrix, dataset_by_class)

    def get_predictions_file_name(self, fold_number):
        """
        Gets the name of the predictions file for the given fold.
        :param fold_number: The number of the fold to get the predictions file
        :return: The name of the predictions file for the given fold.
        """
        return '{}/predictions_{}.txt'.format(self.results_folder, fold_number)

    def get_predictions_line_fields(self, line):
        """
        Splits the line from the predictions file to get its fields.
        :param line: A line from the predictions file.
        :return: An array of line fields.
        """
        return line.split(' ')

    def get_expected_intent(self, fields):
        """
        Gets the expected intent from fields of the prediction file line.
        :param fields: The fields from the prediction file line.
        :return: The expected prediction for the line.
        """
        return fields[1]

    def get_other_predictions_from_line(self, line_fields):
        """
        Gets the predicted intents from the line of the predictions file.
        :param line_fields: The fields of the predictions file line.
        :return: An array with the predicted intents and their confidence from the predictions file line.
        """
        return line_fields[2:]

    def get_pairwise_analysis_dir_name(self):
        return '{}/{}'.format(self.results_folder, 'pairwise_analysis')

    def get_pairwise_class_dump_file_name(self, real_class, pred_class):
        """
        Gets the name for the file containing the test examples where WCS should predict real_class but predicted pred_class.
        :param real_class Real class name
        :param pred_class Predicted class name
        :return:  A string representation the file name to store the examples regarding the line real_class x pred_class in the pairwise class table.
        """
        return '{}/{}-{}.csv'.format(self.get_pairwise_analysis_dir_name(), real_class, pred_class)


    def add_prediction_to_matrices(self, expected_intent, prediction, confidence, confusion_matrix, confidence_matrix):
        """
        Adds a prediction to the confidence and confusion matrices.
        :param expected_intent: The expected intent being analyzed.
        :param prediction: The predicted intent to be added.
        :param confidence: The confidence value of the predicted intent.
        :param confusion_matrix: The confusion matrix to add the predicted intent to.
        :param confidence_matrix: The confidence matrix to add the predicted intent to.
        """
        if expected_intent not in confusion_matrix:
            confusion_matrix[expected_intent] = {}
            confidence_matrix[expected_intent] = {}

        if prediction not in confusion_matrix[expected_intent]:
            confusion_matrix[expected_intent][prediction] = 0
            confidence_matrix[expected_intent][prediction] = []

        confusion_matrix[expected_intent][prediction] += 1
        confidence_matrix[expected_intent][prediction].append(confidence)

    def calculate_mean_stddev(self, lst):
        """
        Calculates the mean and standard deviation from a list of values.
        :param lst: The list of values to be used to calculate the mean and standard deviation.
        :return: A tuple of mean and standard deviation values.
        """
        s, ss, n = sum(lst), sum([x * x for x in lst]), len(lst)
        m = s / n
        return m, math.sqrt(sum([(x - m) * (x - m) for x in lst]) / n)  # FIXME USE COMPUTATIONAL FORMULA!

    def write_precision_at_k_file(self, precisions_at_k):
        """
        Writes a text file to the results folder with the prediction at k values.
        :param precisions_at_k: A list of dictionaries that has the predicted accuracies at k.
        """
        result = {}

        for prec_at_k in precisions_at_k:
            for k, accuracy in prec_at_k.items():

                if k not in result:
                    result[k] = []

                result[k].append(accuracy)

        with open('{}/precision_at_k.txt'.format(self.results_folder), 'w', encoding="UTF-8") as precision_at_k_file:
            for k, accuracies in result.items():
                mean, stddev = self.calculate_mean_stddev(accuracies)
                precision_at_k_file.write('{} {} {}\n'.format(k+1, mean, stddev))

    def write_pairwise_file(self, confidence_matrix, confusion_matrix, dataset_by_class):
        """
        Writes a text file to the results folder with the pairwise classification errors information.
        :param confidence_matrix: The confidence matrix for the experiment.
        :param confusion_matrix: The confusion matrix for the experiment.
        :param dataset_by_class: The dataset divided by classes.
        """
        pairwise_matrix = {}
        for expected_prediction in confusion_matrix:
            for actual_prediction, errors in confusion_matrix[expected_prediction].items():
                if expected_prediction != actual_prediction:

                    if expected_prediction in confidence_matrix \
                            and actual_prediction in confidence_matrix[expected_prediction]:
                        confidences = confidence_matrix[expected_prediction][actual_prediction]
                        pairwise_matrix[expected_prediction] = {
                            'prediction': actual_prediction,
                            'errors': errors,
                            'confidence': self.calculate_mean_stddev(confidences)[0]
                        }

        with open('{}/pairwise_class_error.txt'.format(self.results_folder), 'w', encoding="UTF-8") as pairwise_file:
            for real_class in sorted(pairwise_matrix, key=lambda x: (pairwise_matrix[x]['errors'], pairwise_matrix[x]['confidence']), reverse=True):
                pairwise_file.write('{} {} {} {}\n'.format(real_class, pairwise_matrix[real_class]['prediction'],
                                                           pairwise_matrix[real_class]['errors'], pairwise_matrix[real_class]['confidence']))

                if real_class in dataset_by_class:
                    with open(self.get_pairwise_class_dump_file_name(real_class, pairwise_matrix[real_class]['prediction']), 'w', encoding="UTF-8") as dump_file:
                        dump_writer = csv.writer(dump_file)
                        dump_writer.writerows([[example, real_class] for example in dataset_by_class[real_class]])


if __name__ == '__main__':
    parser = ArgParser(description='Generates train and test data, runs a k fold experiment and report the results')

    parser.add_argument('-w', '--workspace_id', required=True, help='IBM Watson Conversation workspace ID')
    parser.add_argument('-u', '--username', required=True, help='IBM Watson Conversation username')
    parser.add_argument('-p', '--password', required=True, help='IBM Watson Conversation password')

    parser.add_argument('-i', '--folds-dir', required=False, help='Directory containing folds to be re-used by the experiments')

    parser.add_argument('--suppress-entities', dest='no_entities', action='store_true', help='Train experiment workspaces without entities')
    parser.set_defaults(no_entities=False)
    parser.add_argument('--suppress-whitespaces', dest='no_whitespaces', action='store_true', help='Train experiment workspaces without whitespaces in the examples')
    parser.set_defaults(no_whitespaces=False)

    parser.add_argument('-l', '--language', required=False, help='Language code to train the system under another language configuration')

    parser.add_argument('-k', '--num-folds', type=int, default=5, help='Number of cross validation folds')
    parser.add_argument('-f', '--results-folder', required=True, help='Directory for storing test results and '
                                                                      'temporary files')

    args = parser.parse_args()

    username = args.username
    password = args.password
    workspace_id = args.workspace_id

    folds_dir = args.folds_dir

    no_entities = args.no_entities
    no_whitespaces = args.no_whitespaces
    language = args.language

    results_folder = args.results_folder
    number_of_folds = args.num_folds

    conversation_manager = ConversationManager(username, password)

    print('Starting the experiment on workspace {}:\n'.format(workspace_id))

    experiment_runner = ExperimentRunner(conversation_manager, results_folder, number_of_folds, workspace_id, folds_dir, no_entities, no_whitespaces, language)

    experiment_runner.run_experiment()

    print('\nExperiment finished! You can find the results on {}'.format(results_folder))
