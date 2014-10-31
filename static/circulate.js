var circulateApp = angular.module("circulateApp", ['angularFileUpload']);

circulateApp.directive('switchable', function() {
  return {
    scope: {
      conference: '=',
      occasionIx: '=',
      tableIx: '=',
      participantIx: '=',
      updateGroupingForTable: '&'
    },
    link: function(scope, element) {
      // Get the native object
      var el = element[0];
      el.draggable = true;

      function setTargetAppearence(target, event) {
        sourceParticipant = scope.conference[scope.conference.dragSourceOccasionIx].tables[scope.conference.dragSourceTableIx][scope.conference.dragSourceParticipantIx];
        targetParticipant = scope.conference[scope.occasionIx].tables[scope.tableIx][scope.participantIx];

        if ((scope.conference.dragSourceOccasionIx != scope.occasionIx || sourceParticipant.fix || targetParticipant.fix) && (sourceParticipant != targetParticipant)) {
          target.classList.add('over-nok');
        } else {
          target.classList.add('over-ok');
        }
        return false;
      };

      function clearTargetAppearance(target) {
        target.classList.remove('over-ok');
        target.classList.remove('over-nok');
        return false;
      };

      el.addEventListener(
        'dragover',
        function(e) {
          e.dataTransfer.dropEffect = 'move';
          // allows us to drop
          if (e.preventDefault) e.preventDefault();
          return setTargetAppearence(this, e);
        },
        false
      );

      el.addEventListener(
        'dragenter',
        function(e) {
          return setTargetAppearence(this, e);
        },
        false
      );

      el.addEventListener(
        'dragleave',
        function(e) {
          return clearTargetAppearance(this);
        },
        false
      );

      el.addEventListener(
        'drop',
        function(e) {
          // Stops some browsers from redirecting.
          if (e.stopPropagation) e.stopPropagation();

          clearTargetAppearance(this);
          sourceParticipant = scope.conference[scope.conference.dragSourceOccasionIx].tables[scope.conference.dragSourceTableIx][scope.conference.dragSourceParticipantIx];
          targetParticipant = scope.conference[scope.occasionIx].tables[scope.tableIx][scope.participantIx];

          if (scope.conference.dragSourceOccasionIx != scope.occasionIx || sourceParticipant.fix || targetParticipant.fix) {
            return false;
          }

          scope.$apply(function(scope) {
            // Switch the data rather than the actual DOM elements
            console.log("Dropping");
            scope.conference[scope.conference.dragSourceOccasionIx].tables[scope.conference.dragSourceTableIx][scope.conference.dragSourceParticipantIx] = targetParticipant;
            scope.conference[scope.occasionIx].tables[scope.tableIx][scope.participantIx] = sourceParticipant;
            scope.updateGroupingForTable({occasionIx: scope.conference.dragSourceOccasionIx, tableIx: scope.conference.dragSourceTableIx});
            scope.updateGroupingForTable({occasionIx: scope.occasionIx, tableIx: scope.tableIx});
          });

          return false;
        },
        false
      );


      el.addEventListener(
        'dragstart',
        function(e) {
          console.log("Starting to drag: " + scope.occasionIx + ", " + scope.tableIx + ", " + scope.participantIx);
          e.dataTransfer.effectAllowed = 'move';

          // Using variables directly on the scope for communicating which participant
          // is dragged is a hack to work around that Chrome won't allow access to the
          // data in the dataTransfer object for all states.
          scope.conference.dragSourceOccasionIx = scope.occasionIx;
          scope.conference.dragSourceTableIx = scope.tableIx;
          scope.conference.dragSourceParticipantIx = scope.participantIx;

          this.classList.add('drag');
          return false;
        },
        false
      );

      el.addEventListener(
        'dragend',
        function(e) {
          this.classList.remove('drag');
          return false;
        },
        false
      );

      el.addEventListener(
        'click',
        function(e) {
          scope.$apply(function(scope) {
            scope.conference[scope.occasionIx].tables[scope.tableIx][scope.participantIx].fix = !scope.conference[scope.occasionIx].tables[scope.tableIx][scope.participantIx].fix;
          });

          return false;
        },
        false
      );
    }
  }
});


circulateApp.controller('CirculateCtrl', function($scope,  $http, $document, $upload) {
  $scope.dataLoaded = false;
  $scope.onFileSelect = function($files) {
    //$files: an array of files selected, each file has name, size, and type.
    // TODO: Restrict to single file
    for (var i = 0; i < $files.length; i++) {
      var file = $files[i];
      $scope.upload = $upload.upload({
        url: '/upload',
        method: 'POST',
        file: file,
      }).progress(function(evt) {
        console.log('percent: ' + parseInt(100.0 * evt.loaded / evt.total));
      }).success(function(data, status, headers, config) {
        console.log("Success! ");
        console.log(data);
        $scope.conference = data.conference;
        $scope.participantNames = data.participant_names;
        $scope.relationsCount = 100;
        $scope.groupNames = data.group_names;
        updateRelationData(data.relations, data.relation_stats);
        $scope.currentOccasionIx = 0;
        $scope.weightMatrix = data.weight_matrix;
        $scope.dataLoaded = true;
        $scope.stepOccasion(0);
        $scope.groupParticipation = data.group_participation;
        updateGroupingData();
        $scope.filename = data.filename;
      }).error(function(data, status, headers, config) {
        console.log("It went to hell! " + data);
      });
    }
  };

  $scope.setOccasion = function(ix) {
    $scope.currentOccasionIx = ix;
    $scope.currentOccasion = $scope.conference[$scope.currentOccasionIx];
    $scope.previousOccasion = $scope.conference[($scope.currentOccasionIx - 1 + $scope.conference.length) % $scope.conference.length];
    $scope.nextOccasion = $scope.conference[($scope.currentOccasionIx + 1) % $scope.conference.length];
  };

  $scope.stepOccasion = function(direction) {
    var occasionIx = ($scope.currentOccasionIx + direction + $scope.conference.length) % $scope.conference.length;
    $scope.setOccasion(occasionIx);
  };

  $scope.simulationTimes = [
    {name:'Refresh statistics', value: 0.0},
    {name:'1 s', value: 1.0},
    {name:'15 s', value: 15.0},
    {name:'1 min', value: 60.0},
    {name:'10 min', value: 600.0},
    {name:'1 h', value: 3600.0}
  ];

  $scope.simulationTime = $scope.simulationTimes[1];
  $scope.penaltyChoices = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 50, 100, 500, 1000];
  $scope.colocPenalty = $scope.penaltyChoices[0];
  $scope.commandInProgress = false;
  $scope.showGroups = true;

  function updateRelationData(allRelations, relationStat) {
    $scope.allRelationStat = relationStat;
    $scope.relations = $scope.allRelationStat.slice(0, $scope.relationsCount);
    $scope.relationData = {}
    for(var i=0; i < allRelations.length; i++) {
      var relationCount = allRelations[i][2];
      if($scope.relationData[relationCount] !== undefined) {
        $scope.relationData[relationCount]++;
      } else {
        $scope.relationData[relationCount] = 1;
      }
    }
  };

  $scope.expandStat = function() {
    $scope.relationsCount += 100;
    $scope.relations = $scope.allRelationStat.slice(0, $scope.relationsCount);
  };

  $scope.runSimulation = function() {
    $scope.commandInProgress = true;
    $http({method: 'POST', url: '/simulate',
           data: {participant_names: $scope.participantNames,
                  conference: $scope.conference,
                  weight_matrix: $scope.weightMatrix,
                  simulation_time: $scope.simulationTime['value'],
                  coloc_penalty: $scope.colocPenalty},
           headers: {"Content-Type": "application/json"}}).
    success(function(data, status, headers, config) {
      console.log("Received response");

      // Copy into the original conference object to avoid that the references
      // to the conference from the directives are not lost
      for(var i = 0; i < $scope.conference.length; i++) {
        $scope.conference[i] = data['conference'][i];
      }
      updateRelationData(data['relations'], data['relation_stats']);
      updateGroupingData();
      $scope.stepOccasion(0);
      console.log("Response processed");
    }).
    error(function(data, status, headers, config) {
      console.log("Error calling simulate!")
    }).
    finally(function(data, status, headers, config) {
      $scope.commandInProgress = false;
    });
  };

  $scope.getResult = function() {
    $http({method: 'POST', url: '/result/excel',
           data: {participant_names: $scope.participantNames,
                  conference: $scope.conference,
                  weight_matrix: $scope.weightMatrix,
                  coloc_penalty: $scope.colocPenalty,
                  filename: $scope.filename},
           headers: {"Content-Type": "application/json"}}).
    success(function(data, status, headers, config) {
      console.log("Received file name ");

      // Dirty hack to trigger download
      angular.element($document[0].body).append("<iframe src='" + data.url + "' style='display: none;'></iframe>");
    }).
    error(function(data, status, headers, config) {
      console.log("Error getting file!")
    });
  };

  $scope.updateGroupingForTable = function(occasionIx, tableIx) {
    var tableGroupingData = [];
    $scope.conference[occasionIx].groupingData[tableIx] = tableGroupingData;
    var table = $scope.conference[occasionIx]['tables'][tableIx];
    for(var p=0; p < table.length; p++) {
      var groupMemberships = $scope.groupParticipation[table[p].id];
      for(var g=0; g < groupMemberships.length; g++) {
        if(tableGroupingData[groupMemberships[g]] !== undefined) {
          tableGroupingData[groupMemberships[g]]++;
        } else {
          tableGroupingData[groupMemberships[g]] = 1;
        }
      }
    }
  };

  function updateGroupingData() {
    for(var i=0; i < $scope.conference.length; i++) {
      $scope.conference[i].groupingData = []
      for(var j=0; j < $scope.conference[i]['tables'].length; j++) {
        $scope.updateGroupingForTable(i, j);
      }
    }
  };

});
