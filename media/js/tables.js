function cleanTablesForEditableGrid() {
    // Remove Action column.
    if ($('th:contains("Actions")')) {
        $('th:contains("Actions")').remove();
        $('td:last-child').remove();
    }

    // Remove Info column.
    if ($('th:contains("Info")')) {
        $('th:contains("Info")').remove();
        $('td:first-child').remove();
    }

    // Strip links and paragraph tags, remove table cell markdown until
    // we do CellRenderers.
    $('#egtable').find('td, th').each(function (i, td) {
        var $td = $(td);
        if ($td.children().length) {
            $td.text($td.children()[0].innerHTML);
        }
        $td.text($td.text().trim());
    });
}


/*
Callback function on change. Send whatever was changed so the change
can be validated and the object can be updated.
*/
function editableGridCallback(rowIndex, columnIndex, oldValue, newValue, row) {
    var postData = {};
    var csrfToken = $('#view-metadata').attr('data-csrfToken');
    postData[editableGrid.getColumnName(columnIndex)] = newValue;
    postData.csrfmiddlewaretoken = csrfToken;
    $.post($(row).attr('data-url'), postData, function(resp) {
        if (resp && resp.error) {
            $(row).after($('<tr></tr>').html(resp.error[0]));
        }
    }, 'json');
}


function enableEditableGrid() {
    var $eg = $('#eg');
    if (!$eg) {
        return;
    }

    cleanTablesForEditableGrid();
    editableGrid = new EditableGrid("My Editable Grid");
    editableGrid.loadJSONFromString($eg.attr('data-metadata'));
    editableGrid.modelChanged = editableGridCallback;
    editableGrid.attachToHTMLTable('egtable');
    editableGrid.renderGrid();
}


$(document).ready(function() {
    var $enableEg = $('#enable-eg');
    if ($enableEg.length) {
        $enableEg[0].reset();

        // Enable editable grid on checkbox.
        $enableEg.find('input').removeAttr('disabled').change(function() {
            $this = $(this);
            if ($this.attr('checked')) {
                enableEditableGrid();
                $this.attr('disabled', true);
            }

            $('#enable-eg').remove();
            $('.spreadsheet-mode').show();
        });
    }
});
