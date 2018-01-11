function get_style(p) {
    if (p.prediction_occurred === "Won")
        return "won";
    else if (p.prediction_occurred === "Lost")
        return "lost";
    else if (p.prediction_occurred === "Fulfilled")
        return "won";
    else if (p.prediction_occurred === "Not Fulfilled")
        return "lost";
    else if ((p.opponent_confirmed === false && p.role === "opponent") ||
        (p.witness_confirmed === false && p.role === "witness"))
        return "waitingforconfirmation";
    else return "";
}

function get_role_style(p) {
    if (p.comment !== "")
        return "waitingforconfirmationtext";
    else return "";
}

function showPending(status) {
    $("#ownership_selector").val(status);
    select_changed();
}

function put_stats(data) {
    const w_div = $("#warnings");
    w_div.empty();
    const pending_confirmation = data.pending_confirmation;
    const pending_resolution = data.pending_resolution;
    if (pending_confirmation !== 0)
        w_div.append('<div class="warning"><a href="javascript:showPending(\'pending\')">' + pending_confirmation + ' wager(s) is waiting for your confirmation</a></div>')
    if (pending_resolution !== 0)
        w_div.append('<div class="warning"><a href="javascript:showPending(\'notresolved\')">' + pending_resolution + ' wager(s) is waiting for your decision</a></div>')
}

function put_data(refresh_if_no, data) {
    const p_div = $("#predictions");
    p_div.empty();
    for (var i in data.predictions) {
        const p = data.predictions[i];
        p_div.append('<div style="grid-column: 1"' + ' class="' + get_style(p) + '"><a href="' + p.link + '">' + p.title + '</a></div>');
        p_div.append('<div class="' + get_style(p) + '">' + p.date + '</div>');
        p_div.append('<div class="' + get_style(p) + '">' + p.prediction_occurred + '</div>');
        p_div.append('<div class="' + get_style(p) + '">' + p.role + '</div>');
        p_div.append('<div class="' + get_style(p) + ' ' + get_role_style(p) + '"><a href="' + p.link + '">' + p.comment + '</a></div>');
    }
    if (data.predictions.length === 0 && refresh_if_no) {
        if ($("#ownership_selector").val() !== "all") {
            $("#ownership_selector").val("all");
            select_changed();
        } else if ($("#status_selector").val() !== "all") {
            $("#status_selector").val("all");
            select_changed();
        } else if ($("#date_selector").val() !== "all") {
            $("#date_selector").val("all");
            select_changed();
        }
    }
}

function select_changed(refresh_if_no) {
    const put_data_bind = put_data.bind(null, refresh_if_no);
    $.ajax({
        dataType: 'json',
        url: "/predictions" +
        "?status=" + $("#status_selector").val()
        + "&role=" + $("#ownership_selector").val()
        + "&date=" + $("#date_selector").val(),
        success: put_data_bind
    });
}


$(document).ready(function () {
    select_changed(true);
    $.ajax({
        dataType: 'json',
        url: "/statistics",
        success: put_stats
    });

});
