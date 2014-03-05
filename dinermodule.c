#include "Python.h"
#include <sys/time.h>
#include <stdlib.h>
#include <unistd.h>

static double get_time() {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (double)tv.tv_sec + (0.000001f * tv.tv_usec);
}

static void scramble(int *buf, int length) {
    int i, from_index, temp;
    for(i = length - 1; i > 0; i--) {
        from_index = rand() % (i + 1);
        temp = buf[i];
        buf[i] = buf[from_index];
        buf[from_index] = temp;
    }
}

static void change_place(int ix1, int ix2, int *arr) {
    int temp = arr[ix1];
    arr[ix1] = arr[ix2];
    arr[ix2] = temp;
}

static double calculate_table_score(int *participants, int *weights, int weights_size,
                                    int t_offset, int t_size) {
    int accumulator = 0;
    for(int j=0; j<t_size; j++) {
        for(int k=0; k<j; k++) {
            accumulator += weights[(weights_size * participants[t_offset+j]) + participants[t_offset+k]];
        }
    }

    return ((double)accumulator) / t_size;
}


static int climb(int *participants,
                 int participant_count,
                 int *table_sizes,
                 int table_sizes_count,
                 int *weights,
                 int weights_size) {
  int t1_offset = 0;

  for(int t1_ix=0; t1_ix<table_sizes_count; t1_ix++) {
     double t1_w1 = calculate_table_score(participants, weights, weights_size, t1_offset, table_sizes[t1_ix]);
     for(int p1_ix=t1_offset; p1_ix<t1_offset+table_sizes[t1_ix]; p1_ix++) {
        int t2_offset = t1_offset + table_sizes[t1_ix];
        for(int t2_ix=t1_ix+1; t2_ix<table_sizes_count; t2_ix++) {
           double t2_w1 = calculate_table_score(participants, weights, weights_size, t2_offset, table_sizes[t2_ix]);
           for(int p2_ix=t2_offset; p2_ix<t2_offset+table_sizes[t2_ix]; p2_ix++) {
              change_place(p1_ix, p2_ix, participants);
              double t1_w2 = calculate_table_score(participants, weights, weights_size, t1_offset, table_sizes[t1_ix]);
              double t2_w2 = calculate_table_score(participants, weights, weights_size, t2_offset, table_sizes[t2_ix]);
              if((t1_w2 + t2_w2) < (t1_w1 + t2_w1)) {
                 return 1;
              } else {
                change_place(p1_ix, p2_ix, participants);
              }
           }
           t2_offset += table_sizes[t2_ix];
        }
     }
     t1_offset += table_sizes[t1_ix];
  }

  return 0;
}

static double calculate_score(int *participants,
                              int participant_count,
                              int *table_sizes,
                              int table_sizes_count,
                              int *weights,
                              int weights_size) {
    double result = 0.0;
    int i, table_size;
    int pos = 0;

    for(i=0; i < table_sizes_count; i++) {
        table_size = table_sizes[i];
        result += calculate_table_score(participants, weights, weights_size, pos, table_size);
        pos += table_size;
    }

    return result;
}

static PyObject *calc_tables(PyObject *self, PyObject *args) {
    double execution_time, stop_time, best_score_random, score, score_climbing, best_score_climbing;
    PyObject *weights, *participants, *table_sizes, *outer_list, *inner_list, *participants_list, *table_sizes_list;
    Py_ssize_t i, j, participant_count, table_sizes_count, weights_size;
    int *cweights, *cparticipants, *ctable_sizes, *best_participants;
    int iteration_count = 0;
    int participant_array_size;

    if (!PyArg_ParseTuple(args, "dOOO", &execution_time, &weights, &participants, &table_sizes))
        return NULL;

    /* Weights */
    outer_list = PySequence_Fast(weights, "expected a sequence");
    weights_size = PySequence_Size(weights);
    cweights = (int*)malloc(sizeof(int) * weights_size * weights_size);

    for (i = 0; i < weights_size; i++) {
        inner_list = PyList_GET_ITEM(outer_list, i);
        for (j = 0; j < weights_size; j++) {
            cweights[weights_size * i + j] = PyInt_AsLong(PyList_GET_ITEM(inner_list, j));
        }
    }

    /* Participants */
    participants_list = PySequence_Fast(participants, "expected a sequence");
    participant_count = PySequence_Size(participants);
    participant_array_size = sizeof(int) * participant_count;
    cparticipants = (int*)malloc(participant_array_size);
    for (i = 0; i < participant_count; i++) {
        cparticipants[i] = PyInt_AsLong(PyList_GET_ITEM(participants_list, i));
    }

    /* Tables */
    table_sizes_list = PySequence_Fast(table_sizes, "expected a sequence");
    table_sizes_count = PySequence_Size(table_sizes);
    ctable_sizes = (int*)malloc(sizeof(int) * table_sizes_count);
    for (i = 0; i < table_sizes_count; i++) {
        ctable_sizes[i] = PyInt_AsLong(PyList_GET_ITEM(table_sizes_list, i));
    }

    stop_time = get_time() + execution_time;

    best_participants = (int*)malloc(participant_array_size);
    memcpy(best_participants, cparticipants, participant_array_size);
    best_score_random = calculate_score(cparticipants, participant_count, ctable_sizes,
                                        table_sizes_count, cweights, weights_size);
    best_score_climbing = best_score_random;
    while(get_time() < stop_time) {
        scramble(cparticipants, participant_count);
        score = calculate_score(cparticipants, participant_count,
                                ctable_sizes, table_sizes_count, cweights, weights_size);

        if(score < best_score_random) {
            best_score_random = score;

            int climbs = 0;
            while(climb(cparticipants, participant_count, ctable_sizes, table_sizes_count,
                        cweights, weights_size)) {
                climbs++;
            }

            score_climbing = calculate_score(cparticipants, participant_count,
                                             ctable_sizes, table_sizes_count, cweights, weights_size);
            printf("Steps: %i, score before: %f, score after: %f\n", climbs, best_score_random, score_climbing);
            if(score_climbing < best_score_climbing) {
                best_score_climbing = score_climbing;
                memcpy(best_participants, cparticipants, participant_array_size);
            }
        }
        iteration_count++;
    }

    free(cparticipants);
    free(ctable_sizes);
    free(cweights);
    free(best_participants);

    return Py_BuildValue("id", iteration_count, best_score_climbing);
}



static PyMethodDef DinerMethods[] = {
    {"calc_tables",  calc_tables, METH_VARARGS, "Places people by tables"},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


PyMODINIT_FUNC initdinerc(void)
{
    (void) Py_InitModule("dinerc", DinerMethods);
    struct timeval tv;
    gettimeofday(&tv, NULL);
    srandom((int)tv.tv_sec + getpid());
}