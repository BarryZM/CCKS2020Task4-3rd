import numpy as np
from typing import List
from common import Instance
import torch


class Span:
    """
    A class of `Span` where we use it during evaluation.
    We construct spans for the convenience of evaluation.
    """
    def __init__(self, left: int, right: int, type: str):
        """
        A span compose of left, right (inclusive) and its entity label.
        :param left:
        :param right: inclusive.
        :param type:
        """
        self.left = left
        self.right = right
        self.type = type

    def __eq__(self, other):
        return self.left == other.left and self.right == other.right and self.type == other.type

    def __hash__(self):
        return hash((self.left, self.right, self.type))


def evaluate_batch_insts(batch_insts: List[Instance],
                         batch_pred_ids: torch.Tensor,
                         batch_gold_ids: torch.LongTensor,
                         word_seq_lens: torch.LongTensor,
                         idx2label: List[str]) -> np.ndarray:
    """
    Evaluate a batch of instances and handling the padding positions.
    :param batch_insts:  a batched of instances.
    :param batch_pred_ids: Shape: (batch_size, max_length) prediction ids from the viterbi algorithm.
    :param batch_gold_ids: Shape: (batch_size, max_length) gold ids.
    :param word_seq_lens: Shape: (batch_size) the length for each instance.
    :param idx2label: The idx to label mapping.
    :return: numpy array containing (number of true positive, number of all positive, number of true positive + number of false negative)
             You can also refer as (number of correctly predicted entities, number of entities predicted, number of entities in the dataset)
    """
    p = 0
    total_entity = 0
    total_predict = 0
    word_seq_lens = word_seq_lens.tolist()
    for idx in range(len(batch_pred_ids)):
        length = word_seq_lens[idx]
        output = batch_gold_ids[idx][:length].tolist()
        prediction = batch_pred_ids[idx][:length].tolist()
        prediction = prediction[::-1]
        output = [idx2label[l] for l in output]
        prediction =[idx2label[l] for l in prediction]
        batch_insts[idx].prediction = prediction
        # convert to span
        output_spans = set()
        start = -1
        for i in range(len(output)):
            if output[i].startswith("B-"):
                start = i
            if output[i].startswith("E-"):
                end = i
                output_spans.add(Span(start, end, output[i][2:]))
        predict_spans = set()
        for i in range(len(prediction)):
            if prediction[i].startswith("B-"):
                start = i
            if prediction[i].startswith("E-"):
                end = i
                predict_spans.add(Span(start, end, prediction[i][2:]))

        total_entity += len(output_spans)
        total_predict += len(predict_spans)
        p += len(predict_spans.intersection(output_spans))

    # In case you need the following code for calculating the p/r/f in a batch.
    # (When your batch is the complete dataset)
    # precision = p * 1.0 / total_predict * 100 if total_predict != 0 else 0
    # recall = p * 1.0 / total_entity * 100 if total_entity != 0 else 0
    # fscore = 2.0 * precision * recall / (precision + recall) if precision != 0 or recall != 0 else 0

    return np.asarray([p, total_predict, total_entity], dtype=int)


def evaluate_batch_insts_for_entity(batch_insts: List[Instance],
                         batch_pred_ids: torch.Tensor,
                         batch_gold_ids: torch.LongTensor,
                         word_seq_lens: torch.LongTensor,
                         idx2label: List[str],
                         type:str) -> np.ndarray:
    """
    Evaluate a batch of instances and handling the padding positions.
    :param batch_insts:  a batched of instances.
    :param batch_pred_ids: Shape: (batch_size, max_length) prediction ids from the viterbi algorithm.
    :param batch_gold_ids: Shape: (batch_size, max_length) gold ids.
    :param word_seq_lens: Shape: (batch_size) the length for each instance.
    :param idx2label: The idx to label mapping.
    :return: numpy array containing (number of true positive, number of all positive, number of true positive + number of false negative)
             You can also refer as (number of correctly predicted entities, number of entities predicted, number of entities in the dataset)
    """
    type_dict = {'质押': [
        'trigger',
        'sub-org',
        'sub-per',
        'obj-org',
        'obj-per',
        'collateral',
        'date',
        'money',
        'number',
        'proportion'
    ],
    '股份股权转让':
        [
            'trigger',
            'sub-org',
            'sub-per',
            'obj-org',
            'obj-per',
            'collateral',
            'date',
            'money',
            'number',
            'proportion',
            'target-company'
        ],
    '起诉':
        [
            'trigger',
            'sub-org',
            'sub-per',
            'obj-org',
            'obj-per',
            'date',
        ],
    '投资':
        [
            'trigger',
            'sub',
            'obj',
            'money',
            'date',
        ],
    '减持':
        [
            'trigger',
            'sub',
            'title',
            'date',
            'share-per',
            'share-org',
            'obj',
        ],
    '收购':
        [
            'trigger',
            'sub-org',
            'sub-per',
            'obj-org',
            'way',
            'date',
            'money',
            'number',
            'proportion',
        ],
    '判决':
        [
            'trigger',
            'sub-per',
            'sub-org',
            'institution',
            'obj-per',
            'obj-org',
            'date',
            'money',
        ],
    '担保':
        [
            'trigger',
            'sub-per',
            'sub-org',
            'amount',
            'obj-org',
            'date',
            'way',
        ],
    '中标':
        [
            'trigger',
            'sub',
            'obj',
            'amount',
            'date',
        ],
    '签署合同':
        [
            'trigger',
            'sub-per',
            'sub-org',
            'amount',
            'obj-org',
            'obj-per',
            'date',
        ]}
    p_list = [0] * len(type_dict[type])
    total_entity_list = [0] * len(type_dict[type])
    total_predict_list = [0] * len(type_dict[type])

    # p = 0
    # total_entity = 0
    # total_predict = 0
    word_seq_lens = word_seq_lens.tolist()
    for idx in range(len(batch_pred_ids)):
        length = word_seq_lens[idx]
        output = batch_gold_ids[idx][:length].tolist()
        prediction = batch_pred_ids[idx][:length].tolist()
        prediction = prediction[::-1]
        output = [idx2label[l] for l in output]
        prediction =[idx2label[l] for l in prediction]
        batch_insts[idx].prediction = prediction
        # convert to span
        output_spans_list = []
        for i in range(len(type_dict[type])):
            output_spans_list.append(set())
        # output_spans = set()
        start = -1
        for i in range(len(output)):
            if output[i].startswith("B-"):
                start = i
            if output[i].startswith("E-"):
                end = i
                role = output[i][2+len(type):]
                output_spans_list[type_dict[type].index(role)].add(Span(start, end, output[i][2:]))
        predict_spans_list = []
        for i in range(len(type_dict[type])):
            predict_spans_list.append(set())
        # predict_spans = set()
        for i in range(len(prediction)):
            if prediction[i].startswith("B-"):
                start = i
            if prediction[i].startswith("E-"):
                end = i
                role = prediction[i][2 + len(type):]
                predict_spans_list[type_dict[type].index(role)].add(Span(start, end, prediction[i][2:]))

        for j in range(len(type_dict[type])):
            total_entity_list[j] += len(output_spans_list[j])
        for k in range(len(type_dict[type])):
            total_predict_list[k] += len(predict_spans_list[k])
        for m in range(len(type_dict[type])):
            p_list[m] += len(predict_spans_list[m].intersection(output_spans_list[m]))
        # total_entity += len(output_spans)
        # total_predict += len(predict_spans)
        # p += len(predict_spans.intersection(output_spans))

    # In case you need the following code for calculating the p/r/f in a batch.
    # (When your batch is the complete dataset)
    # precision = p * 1.0 / total_predict * 100 if total_predict != 0 else 0
    # recall = p * 1.0 / total_entity * 100 if total_entity != 0 else 0
    # fscore = 2.0 * precision * recall / (precision + recall) if precision != 0 or recall != 0 else 0

    return np.asarray([p_list, total_predict_list, total_entity_list], dtype=int).transpose()