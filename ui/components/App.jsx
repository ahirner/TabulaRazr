if (Meteor.isClient) {
  // This code is executed on the client only
 
  Meteor.startup(() => {
    // Use Meteor.startup to render the component after the page is ready
    ReactDOM.render(<Browser />, document.getElementById("render-target"));
  });
}