/* Each execution gets the same independent sample database. */
importScripts('./vendor/sql-wasm.js');
let SQL, seedSQL;
self.onmessage = async ({data}) => {
  if (data.type === 'init') {
    try {
      seedSQL = data.seedSQL;
      SQL = await initSqlJs({locateFile: name => new URL('./vendor/' + name, self.location.href).href});
      const db = new SQL.Database();
      db.run(seedSQL);
      const tables = db.exec("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")[0];
      db.close();
      self.postMessage({type:'ready', tables});
    } catch (error) { self.postMessage({type:'initError',error:error.message}); }
    return;
  }
  if (data.type === 'run') {
    let db;
    try {
      if (!SQL) throw new Error('查詢引擎尚未就緒');
      db = new SQL.Database(); db.run(seedSQL);
      const started = performance.now();
      const before = db.exec('SELECT total_changes()')[0].values[0][0];
      const results = [];
      for (const statement of db.iterateStatements(data.sql)) {
        const columns = statement.getColumnNames();
        const values = [];
        let rowCount = 0;
        while (statement.step()) {
          if (rowCount < 300) values.push(statement.get());
          rowCount++;
        }
        if (columns.length) results.push({columns, values, rowCount});
      }
      const changed = db.exec('SELECT total_changes()')[0].values[0][0] - before;
      self.postMessage({type:'result',id:data.id,results,changed,ms:performance.now()-started});
    } catch (error) { self.postMessage({type:'result',id:data.id,error:error.message}); }
    finally { if (db) db.close(); }
  }
};
