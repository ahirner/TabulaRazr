Browser = React.createClass({
  getInitialState() {
    //TODO: obviously this is dumb, will look into better architecture.
    this.getTables();

    return {
      tables: []
    }
  },

  getTables() {
    return HTTP.call("GET","http://0.0.0.0:7081/api/get_similar_tables_all/muni_bonds/2012_msw_dat_tbls/1648", {},
      (error, result) => {
        if (!error) {
          console.log(JSON.parse(result.content));
          this.setState({tables: JSON.parse(result.content)});
        }
      }
    );
  },

  setActiveTable(event) {
  	console.log(event);
  },
 
  renderTables() {
    if (!this.state.tables.length) {
      return <li>Unfortunately, we could not retrieve any tables.</li>;
    } else {
      return this.state.tables.map((table) => {
        return <Table table={table} key={table._id.table_id} handleClick={this.setActiveTable} />;
      });
    }
  },
 
  render() {
    return (
      <div className="container">
        <div className="left">
          <h3>Similar Tables in Project</h3>
          <ul>
            {this.renderTables()}
          </ul>
        </div>

        <div className="right">
        	<h3>Viewing Table: </h3>
        </div>
      </div>
    );
  }
});