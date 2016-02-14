(function() {
	angular.
	module('tabularazr').
	controller('HomeCtrl', ['$scope', '$http', 'Upload', HomeCtrl]);

	function HomeCtrl($scope, $http, Upload) {
	  console.log ('fuck');
	    $scope.files = "";
	    $scope.fuck = function(){
	      console.log ('fuck');
	      console.log ($scope.files);
	      $scope.uploadFiles(decodeURIComponent($scope.files[0].lfDataUrl));
	    }
        /*$scope.uploadfile = function(){
            console.log ($scope.files);
            console.log ($scope.files[0].lfFile);
            //var blob = new Blob([1,2,3]);
            upload({
              url: '/',
              method: 'POST',
              data: {
                //anint: 123,
                //aBlob: blob, // Only works in newer browsers
                aFile: $scope.files[0].lfFile, // a jqLite type="file" element, upload() will extract all the files from the input and put them into the FormData object before sending.
              }
            }).then(
              function (response) {
                console.log(response.data); // will output whatever you choose to return from the server on a successful upload
              },
              function (response) {
                  console.error(response); //  Will return if status code is above 200 and lower than 300, same as $http
              }
            );
        }*/
        
    $scope.uploadFiles = function (file) {
      console.log (file.type);
      //if (files && files.length) {
        console.log ('fuck');
        /*Upload.upload({
            url: '',
            data: {file: files},
            method: 'POST'
        }).then(function (resp) {
            console.log('Success ' + resp.config.data.file.name + 'uploaded. Response: ' + resp.data);
        }, function (resp) {
            console.log('Error status: ' + resp.status);
            console.log (resp);
        }, function (evt) {
            var progressPercentage = parseInt(100.0 * evt.loaded / evt.total);
            //console.log('progress: ' + progressPercentage + '% ' + evt.config.data.file.name);
        });*/
        /*Upload.http({
          url: '',
          headers : {
            'Content-Type': file.type
          },
          data: file
        }).then(function (resp) {
            console.log('Success ' + resp.config.data.file.name + 'uploaded. Response: ' + resp.data);
        }, function (resp) {
            console.log('Error status: ' + resp.status);
            console.log (resp);
        }, function (evt) {
            var progressPercentage = parseInt(100.0 * evt.loaded / evt.total);
            console.log('progress: ' + progressPercentage + '% ' + evt.config.data.file.name);
        });*/
        $scope.post('', {file: file});
      //}
    }
    
    $scope.post = function (path, params, method) {
        method = method || "post"; // Set method to post by default if not specified.
    
        // The rest of this code assumes you are not using a library.
        // It can be made less wordy if you use one.
        var form = document.createElement("form");
        form.setAttribute("method", method);
        form.setAttribute("action", path);
        form.setAttribute("enctype", "multipart/form-data");
    
        for(var key in params) {
            if(params.hasOwnProperty(key)) {
                var hiddenField = document.createElement("input");
                hiddenField.setAttribute("type", "hidden");
                hiddenField.setAttribute("name", key);
                hiddenField.setAttribute("value", params[key]);
                if (key=='file') hiddenField.setAttribute("type", key);
    
                form.appendChild(hiddenField);
                console.log (hiddenField);
             }
        }
        var hiddenField = document.createElement("select");
        hiddenField.setAttribute("name", "project");
                hiddenField.setAttribute("value", "muni_bonds");
                form.appendChild(hiddenField);
        document.body.appendChild(form);
        console.log (form.attributes.getNamedItem("enctype"));
        console.log (form);
        console.log (decodeURIComponent(document.getElementById('file').value));
        /*//form.submit();*/
    }
	}
})();