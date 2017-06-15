function (key, values, rereduce) {
  var best = values[0];
  var curr_val;
  for (var i in values) {
    curr_val = values[i];
    if (curr_val.timestamp > best.timestamp) {
      best = curr_val;
    }
  }
  return best;
}

