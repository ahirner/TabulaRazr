(function() {
	angular.
	module('tabularazr').
	controller('BrowserCtrl', ['$scope', '$http', BrowserCtrl]);

	function BrowserCtrl($scope, $http) {

		$http.get('http://0.0.0.0:8000/get_tables/test.pdf.txt?project=').then(function(response) {
			$scope.test = response.data;
		});

		$scope.model = {
			message: 'Hello World'
		};

		$scope.change = function() {
			
			$scope.model.message = 'Hey Look I updated';
		}
	}
})();