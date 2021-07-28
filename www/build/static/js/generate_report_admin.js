



function get_mainpage(){
    window.location.href =  document.location.origin;
}



function validate()
{
    if (!$("#selected_year").val() ||  !$("#selected_month").val() ||  !$("#selected_employee").val()){
        return false;
    }
    return true;
}


function generate_report()
{
    if (!validate())
    {
         $("#responseModal-msg").text("Please select year, month and employee");
         $("#responseModal").modal("show");
         return;
    }

    $.LoadingOverlay("show", {
        size: 8,
        background: "rgba(112, 112, 112, 0.8)",
        textClass: "spinner_text"
    });

    const formData = new FormData();
    formData.append("selected_year", $("#selected_year").val());
    formData.append("selected_month", $("#selected_month").val());
    formData.append("selected_employee", $("#selected_employee").val());

    $.ajax({
        type: "POST",
        contentType: false,
        processData: false,
        url: "/generate_report",
        data: formData,
        success: function(res) {
           $.LoadingOverlay("hide");
           if (res.status === "1") {
                create_report_table(res.extra_data);
           } else {
             $("#responseModal-msg").text(res.extra_data);
             $("#responseModal").modal("show");
           }
        },
        error: function(request, textstatus, error) {
            $.LoadingOverlay("hide");
            $("#responseModal-msg").text("Server unavailable currently. Please try again later.")
            $("#responseModal").modal("show");
        },
        timeout: 90 * 1000
    });
}


function create_report_table(data){
    var myTable = $('#report_table').DataTable({
        "bDestroy": true,
        "paging": true,
        "lengthChange": false,
        "ordering": true,
        "autoWidth": true,
        "searching": true,
        "paginate": false,
        "scrollX": true,
        "info": true,
        "order": [[ 0, "desc" ]],
        "data": [],
        "columns": [
        {
            "title": "Year",
        },
        {
            "title": "Month",
        },
        {
            "title": "Day",
        },
        {
            "title": "Entry",
        },
        {
            "title": "Exit",
        },
        {
            "title": "Total",
        },
        ],

    });
    var year = data.year
    var month = data.month
    var data = data.data
    myTable.clear();
    $.each(data, function(key, value) {
        var td1 = year
        var td2 = month
        var td3 = key
        var td4 = ("entry" in value) ? value.entry : ""
        var td5 = ("exit" in value) ? value.exit : ""
        var td6 = ("total" in value) ? value.total : ""
        myTable.row.add([td1, td2, td3, td4, td5, td6]);

    });
    myTable.draw();

    if( $("#download_report_btn").css('visibility') != 'visible') {
        $("#download_report_btn").css("visibility", "visible").hide();
        $("#download_report_btn").fadeIn();
    }

}




function download_report()
{
    if (!validate())
    {
         $("#responseModal-msg").text("Please select year, month and employee");
         $("#responseModal").modal("show");
         return;
    }
    window.open(
      '/download_report?selected_year=' + $("#selected_year").val() + "&selected_month=" + $("#selected_month").val() + "&selected_employee=" + $("#selected_employee").val(),
      '_blank'
    );
}