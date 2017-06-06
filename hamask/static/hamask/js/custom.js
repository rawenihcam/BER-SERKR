function group_order_up(p_id) {
    $.ajax({
        url: '/ajax/reorder_group/',
        data: {
          'group_id': p_id,
          'order': "UP"
        },
        dataType: 'json',
        success: function (data) {
        }
      });
}