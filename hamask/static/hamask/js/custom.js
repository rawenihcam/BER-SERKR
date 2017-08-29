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
                $('#div_'+p_id).hide("fast");
            }
        }
    });
}

function group_change_name(p_id, p_name) {
    if (p_name != ''){        
        $.ajax({
            url: '/ajax/update_group/',
            data: {
              'group_id': p_id,
              'group_name': p_name
            },
            dataType: 'json',
            success: function (data) {
                if (typeof data.group_id !== "undefined"){
                    $('#span_group_'+p_id).text(p_name);
                    $('#group_name_'+p_id).hide();
                    $('#h_group_'+p_id).show();
                }
            }
        });
    }else{
        $('#group_name_'+p_id).hide().val($('#span_group_'+p_id).text());
        $('#h_group_'+p_id).show();
    }
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
                $('#tr_'+p_id).hide("fast");
                $('#tr_'+p_id+' > td.can_delete > input').prop('checked', true);
            }
        }
    });
}

function exercise_field_display(p_field) {
    if (p_field != '') {
        rep_scheme = $(p_field).val();
        rep_scheme_id = $(p_field).attr('id');
        base_id = rep_scheme_id.replace(/rep_scheme$/, '');
        
        percentage = $('#'+base_id+'percentage');
        rpe = $('#'+base_id+'rpe');
        weight = $('#'+base_id+'weight');
        
        if (rep_scheme == 'MAX_PERCENTAGE'){
            percentage.prop('disabled', false);
            rpe.prop('disabled', true).val('');
            weight.prop('disabled', true).val('');
        }
        else if (rep_scheme == 'RPE'){
            percentage.prop('disabled', true).val('');
            rpe.prop('disabled', false);
            weight.prop('disabled', true).val('');
        }
        else if (rep_scheme == 'WEIGHT'){
            percentage.prop('disabled', true).val('');
            rpe.prop('disabled', true).val('');
            weight.prop('disabled', false);
        }
        else{
            percentage.prop('disabled', true).val('');
            rpe.prop('disabled', true).val('');
            weight.prop('disabled', true).val('');
        }
    }else{
        $('div.rep_scheme > div > select').each(function(){
            exercise_field_display(this);
        });
    }
}

/* Workout_Log */
function exercise_log_order(p_id, p_order) {
    $.ajax({
        url: '/ajax/reorder_exercise_log/',
        data: {
          'exercise_log_id': p_id,
          'order': p_order
        },
        dataType: 'json',
        success: function (data) {
            if (typeof data.exercise_log_id !== "undefined"){
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

function exercise_log_delete(p_id) {
    $.ajax({
        url: '/ajax/delete_exercise_log/',
        data: {
          'exercise_log_id': p_id
        },
        dataType: 'json',
        success: function (data) {
            if (typeof data.exercise_log_id !== "undefined"){
                $('#tr_'+p_id).hide("fast");
                $('#tr_'+p_id+' > td.can_delete > input').prop('checked', true);
            }
        }
    });
}

/*** GLOBAL ****/
/* Formsets */
function formset_add_more(p_selector, p_type) {
    var newElement = $(p_selector).clone(true);
    var total = $('#id_' + p_type + '-TOTAL_FORMS').val();
    
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
    $('#id_' + p_type + '-TOTAL_FORMS').val(total);
    $(p_selector).after(newElement);
}

/* Misc */
function escapeHtml(text) {
    'use strict';
    return text.replace(/[\"&'\/<>]/g, function (a) {
        return {
            '"': '&quot;', '&': '&amp;', "'": '&#39;',
            '/': '&#47;',  '<': '&lt;',  '>': '&gt;'
        }[a];
    });
}