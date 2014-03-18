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

    if (!PyArg_ParseTuple(args, "dOOO", &data->execution_time, &weights, &participants, &table_sizes)) {
        return NULL;
    }

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

typedef struct Occasion {
   int* participants;
   Py_ssize_t  participant_count;
   int* table_sizes;
   Py_ssize_t  table_size_count;
} Occasion;

static void destroy_occasions(Occasion *occasions, int occasion_count) {
    for(int i=0; i<occasion_count; i++) {
        free(occasions[i].participants);
        free(occasions[i].table_sizes);
    }

    free(occasions);
}

static Py_ssize_t create_occasions(PyObject *participants_per_occasion,
                            PyObject *table_sizes_per_occasion,
                            Occasion **occasions) {
    PyObject *outer_participants = PySequence_Fast(participants_per_occasion, "expected a sequence");
    PyObject *outer_table_sizes = PySequence_Fast(table_sizes_per_occasion, "expected a sequence");

    Py_ssize_t occasion_count = PySequence_Size(participants_per_occasion);
    assert(occasion_count == PySequence_Size(table_sizes_per_occasion));
    *occasions = (Occasion*)malloc(sizeof(Occasion) * occasion_count);

    for (Py_ssize_t i = 0; i < occasion_count; i++) {
        (*occasions)[i].participant_count = pylist_to_array(PyList_GET_ITEM(outer_participants, i),
                                                           &((*occasions)[i].participants));

        (*occasions)[i].table_size_count = pylist_to_array(PyList_GET_ITEM(outer_table_sizes, i),
                                                           &((*occasions)[i].table_sizes));
    }

    return occasion_count;
}

typedef struct Conference {
   Occasion *occasions;
   Py_ssize_t occasion_count;
   int *weights;
   Py_ssize_t  weight_count;
   int  seating_badness;
   double execution_time;
} Conference;

static void destroy_conference(Conference *conference) {
    destroy_occasions(conference->occasions, conference->occasion_count);
    free(conference->weights);
    free(conference);
}

static Conference* create_conference(PyObject *args) {
    PyObject *weights, *participants_per_occasion, *table_sizes_per_occasion;
    Conference *conference = (Conference*)malloc(sizeof(Conference));


    if (!PyArg_ParseTuple(args, "diOOO", &conference->execution_time,
                          &conference->seating_badness,
                          &weights, &participants_per_occasion,
                          &table_sizes_per_occasion)) {
        return NULL;
    }

    conference->occasion_count = create_occasions(participants_per_occasion, table_sizes_per_occasion,
                                                  &conference->occasions);
    conference->weight_count = pylistlist_to_array(weights, &conference->weights);

    return conference;
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

static void update_relations(int *relations, int dimension_size, Occasion *occasion) {
    int offset = 0;
    for(int i=0; i<occasion->table_size_count; i++) {
        printf("Table %i\n", i);
        for(int j=0; j<occasion->table_sizes[i]; j++) {
            for(int k=0; k<j; k++) {
                printf("Relation: %i - %i\n", occasion->participants[offset+j], occasion->participants[offset+k]);
                relations[(occasion->participants[offset+j] * dimension_size) +
                          occasion->participants[offset+k]]++;

                /* Relations are symmetrical */
                relations[(occasion->participants[offset+k] * dimension_size) +
                          occasion->participants[offset+j]]++;
            }
        }

        offset += occasion->table_sizes[i];
    }
}

static int* create_relation_matrix(Conference *conference) {
    size_t size = conference->weight_count * conference->weight_count * sizeof(int);
    int *relations = (int*)malloc(size);
    memset((void*)relations, 0, size);
    return relations;
}

static int* scramble_conference(Conference *conference) {
    /* The relations matrix contains a count of the number of times that each person
       has been sitting at the same table as another person at the conference.
       It is really just a redundant (but easier to work with when running optimizations)
       representation of the tables and their participants. */

    int *relations = create_relation_matrix(conference);
    for(int i=0; i<conference->occasion_count; i++) {
        printf("Scrambling occasion %i\n", i);
        scramble(conference->occasions[i].participants, conference->occasions[i].participant_count);
        update_relations(relations, conference->weight_count, &(conference->occasions[i]));
    }

    return relations;
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


static int climb_greedy(SimulationData *data) {
  int t1_offset = 0;
  int best_p1_ix = -1;
  int best_p2_ix = -1;
  double best_diff = 0;

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
                 double diff = (t1_w1 + t2_w1) - (t1_w2 + t2_w2);
                 if (diff > best_diff) {
                    best_diff = diff;
                    best_p1_ix = p1_ix;
                    best_p2_ix = p2_ix;
                 }
              }
              change_place(p1_ix, p2_ix, data->participants);
           }
           t2_offset += data->table_sizes[t2_ix];
        }
     }
     t1_offset += data->table_sizes[t1_ix];
  }

  if (best_diff > 0) {
      change_place(best_p1_ix, best_p2_ix, data->participants);
      return 1;
  }

  return 0;
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
              }
              change_place(p1_ix, p2_ix, data->participants);
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
        pos += data->table_sizes[i];
    }

    return result;
}

static PyObject *array_to_pylist(int *arr, int length) {
    PyObject *list = PyTuple_New(length);
    for(int i=0; i<length; i++) {
        PyTuple_SetItem(list, i, PyInt_FromLong(arr[i]));
    }

    return list;
}

static PyObject *conference_to_pylist(int** participants, Conference *conference) {
    PyObject *list = PyTuple_New(conference->occasion_count);
    for(int i=0; i<conference->occasion_count; i++) {
        PyTuple_SetItem(list, i, array_to_pylist(participants[i],
                                                 conference->occasions[i].participant_count));
    }

    return list;
}


static void optimize_conference(Conference *conference, int *relations) {
/*
Loop over all tables at all occasions
 - Find the best move (if it exists), moves can only be made within a occasion but is measured
   against all other possible moves during the whole conference.
   Test occurence_count * n2/2 moves. More or less like climb_greedy but over the whole conference.

Make the best move, if no move exist then finish.

*/

}

static unsigned long int calculate_conference_score(Conference *conference, int *relations) {
    unsigned long int score = 0;
    for(int i=0; i < (conference->weight_count * conference->weight_count); i++) {
        if(relations[i] > 1) {
            score += conference->weights[i] * (relations[i] - 1) * conference->seating_badness;
        } else if(relations[i] == 1) {
            score += conference->weights[i];
        }
    }

    return score;
}

static void copy_participants(int **participants, Conference *conference) {
    for(int i = 0; i < conference->occasion_count; i++) {
        memcpy(participants[i], conference->occasions[i].participants,
               conference->occasions[i].participant_count * sizeof(int));
    }
}

static int **allocate_seating_result(Conference *conference) {
    int** result = (int**)malloc(conference->occasion_count * sizeof(int*));
    for(int i = 0; i < conference->occasion_count; i++) {
        result[i] = (int*)malloc(conference->occasions[i].participant_count * sizeof(int));
    }

    return result;
}

static PyObject *calc_conference(PyObject *self, PyObject *args) {
    Conference *conference = create_conference(args);

    double stop_time = get_time() + conference->execution_time;
    unsigned long int best_score = 0xFFFFFFFFFFFFFFFF;
    int *relations = NULL;
    int *best_relations = create_relation_matrix(conference);
    size_t relation_size = conference->weight_count * conference->weight_count * sizeof(int);
    int **best_seatings = allocate_seating_result(conference);
    while(get_time() < stop_time) {
        relations = scramble_conference(conference);
        optimize_conference(conference, relations);

        unsigned long int conference_score = calculate_conference_score(conference, relations);
        if(conference_score < best_score) {
            best_score = conference_score;
            memcpy(best_relations, relations, relation_size);
            copy_participants(best_seatings, conference);
        }
    }
/*
- Create conference "object"
  - Weight matrix
  - Badness matrix, the same size as the weight matrix
  - X * occasion
    occasion: participant list, table list

 Repeat:
  - Place all participants at random per occasion
  - Calculate the badness table
  - Hill climb the first occasion to find the best placings with the current badness table
  - Hill climb the next occasion...
  - Then start over with the first occasion again, repeat until no more hill climbing is
    possible for any occasion

*/

    printf("\n");

    PyObject *relation_list = array_to_pylist(best_relations,
                                              conference->weight_count * conference->weight_count);
    PyObject *participants_list = conference_to_pylist(best_seatings, conference);

    free(relations);
    destroy_conference(conference);

    return Py_BuildValue("iOO", best_score, participants_list, relation_list);
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
    double accumulated_improvement = 0.0;
    while(get_time() < stop_time) {
        scramble(data->participants, data->participant_count);
        score = calculate_score(data);

//        if(score < best_score_random) {
            best_score_random = score;

            int steps = 0;
            double time_before = get_time();
            while(climb(data)) {
                steps++;
            }

            score_climbing = calculate_score(data);
            double improvement = ((best_score_random - score_climbing)/best_score_random) * 100;
            accumulated_improvement += improvement;
            printf("Climbed, before: %f, after: %f, steps: %i, improvement: %f, time: %f\n",
                   best_score_random, score_climbing, steps,
                   improvement,
                   get_time() - time_before);

            if(score_climbing < best_score_climbing) {
                best_score_climbing = score_climbing;
                memcpy(best_participants, data->participants, participant_array_size);
            }
//        }
        iteration_count++;
    }

    printf("Average improvement: %f\n", accumulated_improvement/iteration_count);
    free(best_participants);
    destroy_simulation_data(data);

    return Py_BuildValue("id", iteration_count, best_score_climbing);
}

static PyMethodDef DinerMethods[] = {
    {"calc_tables",  calc_tables, METH_VARARGS, "Places people by tables"},
    {"calc_conference",  calc_conference, METH_VARARGS, "Places people by tables optimized for the whole conference"},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


PyMODINIT_FUNC initdinerc(void)
{
    (void) Py_InitModule("dinerc", DinerMethods);
    struct timeval tv;
    gettimeofday(&tv, NULL);
    srandom((int)tv.tv_sec + getpid());
}