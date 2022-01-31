var curtemp = new TimeSeries();
var settemp = new TimeSeries();
var settempm = new TimeSeries();
var settempp = new TimeSeries();
var pterm = new TimeSeries();
var iterm = new TimeSeries();
var dterm = new TimeSeries();
var pidval = new TimeSeries();
var lastreqdone = 1;
var timeout;

function refreshinputs() {
	$.getJSON({
		url: "/allstats",
		timeout: 500,
		success: function (resp) {
			console.log(resp);
			$("#inputSetTemp").val(resp.settemp);
			$("#inputSnooze").val(resp.snooze);
			$("#inputSetSteamTemp").val(resp.steamtemp);
			$("#p-value").val(resp.Kp);
			$("#i-value").val(resp.Ki);
			$("#d-value").val(resp.Kd);
		},
	});
}

function resettimer() {
	clearTimeout(timeout);
	timeout = setTimeout(refreshinputs, 30000);
}

function onresize() {
	var h;
	if ($(window).height() * 0.5 > 450) {
		h = 450;
	} else {
		h = $(window).height() * 0.5;
	}

	$("#chart").attr("width", $("#fullrow").width() - 30);
	$("#chart").attr("height", h);
	$("#pidchart").attr("width", $("#fullrow").width() - 30);
	$("#pidchart").attr("height", h);

	if ($(document).width() < 600) {
		$("#toggleadv").html("Adv Stats");
	} else {
		$("#toggleadv").html("Advanced Stats");
	}
}

$(document).ready(function () {
	resettimer();
	$(this).mousemove(resettimer);
	$(this).keypress(resettimer);

	onresize();
	$(window).resize(onresize);

	createTimeline();

	//$(".adv").hide();
	$("#toggleadv").click(function () {
		$(".adv").toggle();
	});

	// $(".timer").hide();
	$("#btnSchedule").click(() => {
		$(".timer").toggle();
	});

	refreshinputs();

	$("#inputSetTemp").change(function () {
		$.post("/settemp", { settemp: $("#inputSetTemp").val() });
	});

	$("#inputSetSteamTemp").change(function () {
		$.post("/setsteamtemp", { steamtemp: $("#inputSetSteamTemp").val() });
	});

	$("[id$=-value]").change(function () {
		$.ajax({
			type: "POST",
			contentType: "application/json",
			url: "/pid",
			data: JSON.stringify({
				p: $("#p-value").val(),
				i: $("#i-value").val(),
				d: $("#d-value").val(),
			}),
		});
	});

	$("#inputSleep").change(function () {
		$.post("/setsleep", { sleep: $("#inputSleep").val() });
	});

	$("#inputWake").change(function () {
		$.post("/setwake", { wake: $("#inputWake").val() });
	});

	$("#btnSnooze").click(function () {
		$.post("/snooze", { snooze: $("#inputSnooze").val() });
		$("#btnSnooze").hide();
		$("#btnSnoozeC").show();
	});

	$("#btnSnoozeC").click(function () {
		$.post("/resetsnooze");
		$("#btnSnooze").show();
		$("#btnSnoozeC").hide();
	});
});

setInterval(function () {
	if (lastreqdone == 1) {
		$.getJSON({
			url: "/allstats",
			timeout: 500,
			success: function (resp) {
				if (resp.snoozeon == true) {
					$("#btnSnooze").hide();
					$("#btnSnoozeC").show();
				} else {
					$("#btnSnooze").show();
					$("#btnSnoozeC").hide();
				}

				// TODO, need to CHANGE this to also get resp.steampin to ensure we are showing the steaming phase
				curtemp.append(new Date().getTime(), resp.temp);
				if (resp.steam) {
					settemp.append(new Date().getTime(), resp.steamtemp);
					settempm.append(new Date().getTime(), resp.steamtemp - 4);
					settempp.append(new Date().getTime(), resp.steamtemp + 4);
				} else {
					settemp.append(new Date().getTime(), resp.settemp);
					settempm.append(new Date().getTime(), resp.settemp - 4);
					settempp.append(new Date().getTime(), resp.settemp + 4);
				}
				pterm.append(new Date().getTime(), resp.pterm);
				iterm.append(new Date().getTime(), resp.iterm);
				dterm.append(new Date().getTime(), resp.dterm);
				pidval.append(new Date().getTime(), resp.pidval);

				$("#curtemp").html(resp.temp.toFixed(2));
				$("#pterm").html(resp.pterm.toFixed(2));
				$("#iterm").html(resp.iterm.toFixed(2));
				$("#dterm").html(resp.dterm.toFixed(2));
				$("#pidval").html(resp.pidval.toFixed(2));
				$("#curr-p-value").html(resp.Kp.toFixed(2));
				$("#curr-i-value").html(resp.Ki.toFixed(2));
				$("#curr-d-value").html(resp.Kd.toFixed(2));
			},
			complete: function () {
				lastreqdone = 1;
			},
		});

		lastreqdone = 0;
	}
}, 100);

function createTimeline() {
	var chart = new SmoothieChart({
		grid: { verticalSections: 3 },
		minValueScale: 1.05,
		maxValueScale: 1.05,
	});
	chart.addTimeSeries(settemp, { lineWidth: 1, strokeStyle: "#ffff00" });
	chart.addTimeSeries(settempm, { lineWidth: 1, strokeStyle: "#ffffff" });
	chart.addTimeSeries(settempp, { lineWidth: 1, strokeStyle: "#ffffff" });
	chart.addTimeSeries(curtemp, { lineWidth: 3, strokeStyle: "#ff0000" });
	chart.streamTo(document.getElementById("chart"), 500);

	var pidchart = new SmoothieChart({
		grid: { verticalSections: 3 },
		minValueScale: 1.05,
		maxValueScale: 1.05,
	});
	pidchart.addTimeSeries(pterm, { lineWidth: 2, strokeStyle: "#ff0000" });
	pidchart.addTimeSeries(iterm, { lineWidth: 2, strokeStyle: "#00ff00" });
	pidchart.addTimeSeries(dterm, { lineWidth: 2, strokeStyle: "#0000ff" });
	pidchart.addTimeSeries(pidval, { lineWidth: 2, strokeStyle: "#2ecac2" });
	pidchart.streamTo(document.getElementById("pidchart"), 500);
}
