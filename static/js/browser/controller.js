(function() {
	angular.
	module('tabularazr').
	controller('BrowserCtrl', ['$scope', '$http', BrowserCtrl]);

	function BrowserCtrl($scope, $http) {
		$scope.sort = {
			rev: true
		};

		$http.get('http://0.0.0.0:8000/get_tables/test.pdf.txt?project=').then(function(response) {
			$scope.test = response.data;
		});

		$scope.model = {
			message: 'Hello World'
		};

		$scope.setSort = function(value) {
			$scope.sort = {
				by: value,
				rev: (value === $scope.sort.by) ? !$scope.sort.rev : $scope.sort.rev
			};
		}

		$scope.data = {
  "meta": 
  [
    {
      "color": "#FiFrFe",
      "subtype": "year",
      "type": "integer",
      "value": "Calendar Year "
    },
    {
      "color": "#FlFeFn",
      "subtype": "none",
      "type": "large_num",
      "value": "Foreclosures "
    },
    {
      "color": "#FlFeFn",
      "subtype": "none",
      "type": "large_num",
      "value": "Total Number of Housing Units(1) "
    },
    {
      "color": "#FsFeFl",
      "subtype": "rate",
      "type": "small_float",
      "value": "% of Total Housing Units "
    }
  ],
  "data": [
    {
      "Calendar Year ": {
        "start": 17,
        "subtype": "year",
        "type": "integer",
        "value": "2010",
        "leftover": [
          "",
          ""
        ]
      },
      "Total Number of Housing Units(1) ": {
        "start": 64,
        "subtype": "none",
        "type": "large_num",
        "value": "1,158,076",
        "leftover": [
          "",
          ""
        ]
      },
      "% of Total Housing Units ": {
        "start": 97,
        "subtype": "rate",
        "type": "small_float",
        "value": "1.16",
        "leftover": [
          "",
          "%"
        ]
      },
      "Foreclosures ": {
        "start": 40,
        "subtype": "none",
        "type": "large_num",
        "value": "13,467",
        "leftover": [
          "",
          ""
        ]
      }
    },
    {
      "Calendar Year ": {
        "start": 17,
        "subtype": "year",
        "type": "integer",
        "value": "2011",
        "leftover": [
          "",
          ""
        ]
      },
      "Total Number of Housing Units(1) ": {
        "start": 64,
        "subtype": "none",
        "type": "large_num",
        "value": "1,161,720",
        "leftover": [
          "",
          ""
        ]
      },
      "% of Total Housing Units ": {
        "start": 97,
        "subtype": "none",
        "type": "small_float",
        "value": "1.05",
        "leftover": [
          "",
          ""
        ]
      },
      "Foreclosures ": {
        "start": 40,
        "subtype": "none",
        "type": "large_num",
        "value": "12,216",
        "leftover": [
          "",
          ""
        ]
      }
    },
    {
      "Calendar Year ": {
        "start": 17,
        "subtype": "year",
        "type": "integer",
        "value": "2012",
        "leftover": [
          "",
          ""
        ]
      },
      "Total Number of Housing Units(1) ": {
        "start": 64,
        "subtype": "none",
        "type": "large_num",
        "value": "1,165,970",
        "leftover": [
          "",
          ""
        ]
      },
      "% of Total Housing Units ": {
        "start": 97,
        "subtype": "none",
        "type": "small_float",
        "value": "0.62",
        "leftover": [
          "",
          ""
        ]
      },
      "Foreclosures ": {
        "start": 41,
        "subtype": "none",
        "type": "large_num",
        "value": "7,195",
        "leftover": [
          "",
          ""
        ]
      }
    },
    {
      "Calendar Year ": {
        "start": 17,
        "subtype": "year",
        "type": "integer",
        "value": "2013",
        "leftover": [
          "",
          ""
        ]
      },
      "Total Number of Housing Units(1) ": {
        "start": 64,
        "subtype": "none",
        "type": "large_num",
        "value": "1,169,095",
        "leftover": [
          "",
          ""
        ]
      },
      "% of Total Housing Units ": {
        "start": 97,
        "subtype": "none",
        "type": "small_float",
        "value": "0.28",
        "leftover": [
          "",
          ""
        ]
      },
      "Foreclosures ": {
        "start": 41,
        "subtype": "none",
        "type": "large_num",
        "value": "3,236",
        "leftover": [
          "",
          ""
        ]
      }
    },
    {
      "Calendar Year ": {
        "start": 17,
        "subtype": "year",
        "type": "integer",
        "value": "2014",
        "leftover": [
          "",
          ""
        ]
      },
      "Total Number of Housing Units(1) ": {
        "start": 64,
        "subtype": "none",
        "type": "large_num",
        "value": "1,176,046",
        "leftover": [
          "",
          ""
        ]
      },
      "% of Total Housing Units ": {
        "start": 97,
        "subtype": "none",
        "type": "small_float",
        "value": "0.17",
        "leftover": [
          "",
          ""
        ]
      },
      "Foreclosures ": {
        "start": 41,
        "subtype": "none",
        "type": "large_num",
        "value": "2,036",
        "leftover": [
          "",
          ""
        ]
      }
    }
  ]
		}

		$scope.sort.by = $scope.data.meta[0].value;
	}
})();