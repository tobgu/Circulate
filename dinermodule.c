#include "Python.h"
#include <sys/time.h>
#include <stdlib.h>
#include <unistd.h>

typedef struct SimulationData {
   int* participants;
   int  participant_count;
   int* table_sizes;
   int  table_size_count;
   int* weights;
   int  weight_count;
   double execution_time;
} SimulationData;

static int pylist_to_array(PyObject *pylist, int **arr) {
    PyObject *list = PySequence_Fast(pylist, "expected a sequence");
    Py_ssize_t count = PySequence_Size(list);
    *arr = (int*)malloc(sizeof(int) * count);

    for (int i = 0; i < count; i++) {
        (*arr)[i] = PyInt_AsLong(PyList_GET_ITEM(list, i));
    }

    return count;
}

static int pylistlist_to_array(PyObject *list, int **arr) {
    PyObject *outer_list = PySequence_Fast(list, "expected a sequence");
    Py_ssize_t count = PySequence_Size(list);
    *arr = (int*)malloc(sizeof(int) * count * count);

    for (int i = 0; i < count; i++) {
        PyObject *inner_list = PySequence_Fast(PyList_GET_ITEM(outer_list, i), "expected a sequence");
        for (int j = 0; j < count; j++) {
            (*arr)[(i * count) + j] = PyInt_AsLong(PyList_GET_ITEM(inner_list, j));
        }
    }

    return count;
}

static SimulationData* create_simulation_data(PyObject *args) {
    PyObject *weights, *participants, *table_sizes;
    SimulationData *data = (SimulationData*)malloc(sizeof(SimulationData));

    if (!PyArg_ParseTuple(args, "dOOO", &data->execution_time, &weights, &participants, &table_sizes))
        return NULL;

    data->participant_count = pylist_to_array(participants, &data->participants);
    data->table_size_count = pylist_to_array(table_sizes, &data->table_sizes);
    data->weight_count = pylistlist_to_array(weights, &data->weights);

    return data;
}

static void destroy_simulation_data(SimulationData *data) {
    free(data->participants);
    free(data->table_sizes);
    free(data->weights);
    free(data);
}

static double get_time(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (double)tv.tv_sec + (0.000001f * tv.tv_usec);
}

static void scramble(int *buf, int length) {
    int from_index, temp;
    for(int i = length - 1; i > 0; i--) {
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

static double calculate_table_score(SimulationData *data, int t_offset, int t_index) {
    int accumulator = 0;
    int t_size = data->table_sizes[t_index];
    for(int j=0; j<t_size; j++) {
        for(int k=0; k<j; k++) {
            accumulator += data->weights[(data->weight_count * data->participants[t_offset+j]) +
                           data->participants[t_offset+k]];
        }
    }

    return ((double)accumulator) / t_size;
}


static int climb(SimulationData *data) {
  int t1_offset = 0;

  for(int t1_ix=0; t1_ix<data->table_size_count; t1_ix++) {
     double t1_w1 = calculate_table_score(data, t1_offset, t1_ix);
     for(int p1_ix=t1_offset; p1_ix<t1_offset+data->table_sizes[t1_ix]; p1_ix++) {
        int t2_offset = t1_offset + data->table_sizes[t1_ix];
        for(int t2_ix=t1_ix+1; t2_ix<data->table_size_count; t2_ix++) {
           double t2_w1 = calculate_table_score(data, t2_offset, t2_ix);
           for(int p2_ix=t2_offset; p2_ix<t2_offset+data->table_sizes[t2_ix]; p2_ix++) {
              change_place(p1_ix, p2_ix, data->participants);
              double t1_w2 = calculate_table_score(data, t1_offset, t1_ix);
              double t2_w2 = calculate_table_score(data, t2_offset, t2_ix);
              if((t1_w2 + t2_w2) < (t1_w1 + t2_w1)) {
                 return 1;
              } else {
                change_place(p1_ix, p2_ix, data->participants);
              }
           }
           t2_offset += data->table_sizes[t2_ix];
        }
     }
     t1_offset += data->table_sizes[t1_ix];
  }

  return 0;
}

static double calculate_score(SimulationData *data) {
    double result = 0.0;
    int pos = 0;

    for(int i=0; i<data->table_size_count; i++) {
        result += calculate_table_score(data, pos, i);
        pos += data->table_sizes[i];;
    }

    return result;
}

static PyObject *calc_tables(PyObject *self, PyObject *args) {
    double best_score_random, score, score_climbing, best_score_climbing;
    int iteration_count = 0;
    SimulationData *data = create_simulation_data(args);
    double stop_time = get_time() + data->execution_time;
    int participant_array_size = data->participant_count * sizeof(int);
    int *best_participants = (int*)malloc(participant_array_size);

    memcpy(best_participants, data->participants, participant_array_size);
    best_score_random = calculate_score(data);
    best_score_climbing = best_score_random;
    while(get_time() < stop_time) {
        scramble(data->participants, data->participant_count);
        score = calculate_score(data);

        if(score < best_score_random) {
            best_score_random = score;

            int steps = 0;
            double time_before = get_time();
            while(climb(data)) {
                steps++;
            }

            score_climbing = calculate_score(data);
            printf("Climbed, before: %f, after: %f, steps: %i, difference: %f, time: %f\n",
                   best_score_random, score_climbing, steps, score_climbing - best_score_random,
                   get_time() - time_before);

            if(score_climbing < best_score_climbing) {
                best_score_climbing = score_climbing;
                memcpy(best_participants, data->participants, participant_array_size);
            }
        }
        iteration_count++;
    }

    free(best_participants);
    destroy_simulation_data(data);

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