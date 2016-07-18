function filterReset(table) {
    table.search("").columns().search("").draw();
}

function filterHasNoGrader(table, column) {
    filterReset(table);
    table.columns(column).search("(No Grader)").draw();
}

function filterHasGrader(table, column) {
    filterReset(table);
    table.columns(column).search("^((?!\(No Grader\)).)*$", true).draw();
}

function filterGreaterThanZero(table, column) {
    filterReset(table);
    table.columns(column).search("^[0-9]*[1-9]$", true).draw();
}

function filterEqualToZero(table, column) {
    filterReset(table);
    table.columns(column).search("^0+$", true).draw();
}

