// App component - represents the whole app
App = React.createClass({
  // This mixin makes the getMeteorData method work
  mixins: [ReactMeteorData],
  // Loads items from the Tables collection and puts them on this.data.tables
  getMeteorData() {
    return {
      tables: Tables.find({}, {sort: {createdAt: -1}}).fetch()
    }
  },

  getInitialState() {
    HTTP.call("GET","http://0.0.0.0:7081/api/get_similar_tables_all/muni_bonds/2012_msw_dat_tbls/1648", {},
      function (error, result) {
        if (!error) {
          Session.set("twizzled", true);
        }

        console.log(result);
      }
    );

    return {

    }
  },

  handleSubmit(event) {
    event.preventDefault();
 
    // Find the text field via the React ref
    var text = ReactDOM.findDOMNode(this.refs.textInput).value.trim();
 
    Tables.insert({
      text: text,
      createdAt: new Date() // current time
    });

    console.log(Tables);
 
    // Clear form
    ReactDOM.findDOMNode(this.refs.textInput).value = "";
  },
 
  renderTables() {
    // this.getMeteorData().tables.map
    if (!this.data.tables.length) {
      return <li>You've finished everything, or need to add a table!</li>;
    } else {
      return this.data.tables.map((table) => {
        return <Table key={table._id} table={table} />;
      });
    }
  },
 
  render() {
    return (
      <div className="container">
        <header>
          <h1>Todo List</h1>

          <form className="new-table" onSubmit={this.handleSubmit} >
            <input
              type="text"
              ref="textInput"
              placeholder="Type to add new tables" />
          </form>
        </header>
        
        <h3>Similar Tables in Project</h3>
        <ul>
          {this.renderTables()}
        </ul>
      </div>
    );
  }
});