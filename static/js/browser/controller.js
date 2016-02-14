(function() {
  angular.
  module('tabularazr').
  controller('BrowserCtrl', ['$scope', '$http', '$state', BrowserCtrl]);

  function BrowserCtrl($scope, $http, $state) {
    var indexOfExtension = $state.params.filename.split('.');
    var filename = indexOfExtension[0];
    var table_id = $state.params.table_id;
    $scope.sort = {
      rev: true
    };

    $scope.switchData = function(item) {
      $scope.data = item;
      var similarUrl = buildUrl(item);
      getSimilar(similarUrl);
    }

    function buildUrl(data) {
      var apiUrlForSimilarTables = "http://0.0.0.0:7081/api/get_similar_tables_all/" +
        (data["_id"].project || "-") + "/" +
        (data["_id"].filename) + "/" +
        (data["_id"].table_id);

      getSimilar(apiUrlForSimilarTables)
    }

    $http.get('http://0.0.0.0:7081/api/get_table/-/' + filename + '/' + table_id).then(function(response) {
      $scope.data = response.data;
      $scope.sort.by = $scope.data.meta[0].value;

      var apiUrlForSimilarTables = buildUrl(response.data);

      getSimilar(apiUrlForSimilarTables)
    });

    function getSimilar(url) {
      if (url) {
        $http.get(url).then(function(response) {
          $scope.similarData = response.data;
        });
      }
    }

    $scope.setSort = function(value) {
      $scope.sort = {
        by: value,
        rev: (value === $scope.sort.by) ? !$scope.sort.rev : $scope.sort.rev
      };
    }
  }
})();