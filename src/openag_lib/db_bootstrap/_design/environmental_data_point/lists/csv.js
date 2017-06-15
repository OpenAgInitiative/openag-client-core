function (head, req) {
  var headers;
  if (req.query.hasOwnProperty("cols")) {
    headers = JSON.parse(req.query.cols);
  }
  else {
    headers = ["timestamp", "variable", "value"];
  }
  start({'headers': {'Content-Type': 'text/csv; charset=utf-8; header=present'}});
  send(headers.join(',') + '\n');
  while (r=getRow()) {
    headers.forEach(function(v,i) {
      send(r.value[v]);
      (i + 1 < headers.length) ? send(',') : send('\n');
    })
  }
}
