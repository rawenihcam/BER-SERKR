/* Workout_Group */
function group_order(p_id, p_order) {
    $.ajax({
        url: '/ajax/reorder_group/',
        data: {
          'group_id': p_id,
          'order': p_order
        },
        dataType: 'json',
        success: function (data) {
            if (typeof data.group_id !== "undefined"){
                row = $('#div_'+p_id);            
                if (p_order == 'UP'){
                    row.insertBefore(row.prev('div.row'));
                }
                else if (p_order == 'DOWN'){
                    row.insertAfter(row.next('div.row'));
                }
            }
        }
      });
}

function group_delete(p_id) {
    $.ajax({
        url: '/ajax/delete_group/',
        data: {
          'group_id': p_id
        },
        dataType: 'json',
        success: function (data) {
            if (typeof data.group_id !== "undefined"){
                $('#div_'+p_id).remove();
            }
        }
    });
}

/* Workout_Exercise */
function exercise_order(p_id, p_order) {
    $.ajax({
        url: '/ajax/reorder_exercise/',
        data: {
          'exercise_id': p_id,
          'order': p_order
        },
        dataType: 'json',
        success: function (data) {
            if (typeof data.exercise_id !== "undefined"){
                row = $('#tr_'+p_id);            
                if (p_order == 'UP'){
                    row.insertBefore(row.prev('tr'));
                }
                else if (p_order == 'DOWN'){
                    row.insertAfter(row.next('tr'));
                }
            }
        }
      });
}

function exercise_delete(p_id) {
    $.ajax({
        url: '/ajax/delete_exercise/',
        data: {
          'exercise_id': p_id
        },
        dataType: 'json',
        success: function (data) {
            if (typeof data.exercise_id !== "undefined"){
                $('#tr_'+p_id).remove();
            }
        }
    });
}

/* GLOBAL */
/* FORMSET */
function add_formset(selector, type) {
    var newElement = $(selector).clone(true);
    var total = $('#id_' + type + '-TOTAL_FORMS').val();
    newElement.find(':input').each(function() {
        var name = $(this).attr('name').replace('-' + (total-1) + '-','-' + total + '-');
        var id = 'id_' + name;
        $(this).attr({'name': name, 'id': id}).val('').removeAttr('checked');
    });
    newElement.find('label').each(function() {
        var newFor = $(this).attr('for').replace('-' + (total-1) + '-','-' + total + '-');
        $(this).attr('for', newFor);
    });
    total++;
    $('#id_' + type + '-TOTAL_FORMS').val(total);
    $(selector).after(newElement);
}