(function ($) {
    function Plot(n, q, r) {
        var u = [];
        var z = {
            colors: ["#edc240", "#afd8f8", "#cb4b4b", "#4da74d", "#9440ed"],
            legend: {
                show: true,
                noColumns: 1,
                labelFormatter: null,
                labelBoxBorderColor: "#ccc",
                container: null,
                position: "ne",
                margin: 5,
                backgroundColor: null,
                backgroundOpacity: 0.85
            },
            xaxis: {
                ticks: null,
                noTicks: 5,
                tickFormatter: defaultTickFormatter,
                tickDecimals: null,
                min: null,
                max: null,
                autoscaleMargin: 0
            },
            yaxis: {
                noTicks: 5,
                ticks: null,
                tickFormatter: defaultTickFormatter,
                min: null,
                max: null,
                autoscaleMargin: 0.02
            },
            points: {show: false, radius: 3, lineWidth: 2, fill: true, fillColor: "#ffffff"},
            lines: {show: false, lineWidth: 2, fill: false, fillColor: null},
            bars: {show: false, lineWidth: 2, barWidth: 1, fill: true, fillColor: null},
            grid: {color: "#545454", backgroundColor: null, tickColor: "#dddddd", labelMargin: 3, clickable: null},
            selection: {mode: null, color: "#e8cfac"},
            shadowSize: 4
        };
        var A = null, overlay = null;
        var B = null, octx = null;
        var C = n;
        var D = {};
        var E = {};
        var F = {left: 0, right: 0, top: 0, bottom: 0};
        var G = 0;
        var H = 0;
        var I = 0;
        var J = 0;
        var K = 0;
        var L = 0;
        var M = 0;
        var N = 0;
        u = parseData(q);
        parseOptions(r);
        fillInSeriesOptions();
        constructCanvas();
        bindEvents();
        findDataRanges();
        calculateRange(D, z.xaxis);
        extendXRangeIfNeededByBar();
        calculateRange(E, z.yaxis);
        calculateTicks(D, z.xaxis);
        calculateTicks(E, z.yaxis);
        calculateSpacing();
        draw();
        insertLegend();
        this.getCanvas = function () {
            return A
        };
        this.getPlotOffset = function () {
            return F
        };
        this.clearSelection = clearSelection;
        this.setSelection = setSelection;
        function parseData(d) {
            var a = [];
            for (var i = 0; i < d.length; ++i) {
                var s;
                if (d[i].data) {
                    s = {};
                    for (var v in d[i])s[v] = d[i][v]
                } else {
                    s = {data: d[i]}
                }
                a.push(s)
            }
            return a
        }

        function parseOptions(o) {
            $.extend(true, z, o)
        }

        function constructCanvas() {
            I = C.width();
            J = C.height();
            C.html("");
            C.css("position", "relative");
            if (I <= 0 || J <= 0)throw"Invalid dimensions for plot, width = " + I + ", height = " + J;
            A = jQuery('<canvas width="' + I + '" height="' + J + '"></canvas>').appendTo(C).get(0);
            if (jQuery.browser.msie)A = window.G_vmlCanvasManager.initElement(A);
            B = A.getContext("2d");
            overlay = jQuery('<canvas style="position:absolute;left:0px;top:0px;" width="' + I + '" height="' + J + '"></canvas>').appendTo(C).get(0);
            if (jQuery.browser.msie)overlay = window.G_vmlCanvasManager.initElement(overlay);
            octx = overlay.getContext("2d")
        }

        function bindEvents() {
            if (z.selection.mode != null) {
                $(overlay).mousedown(onMouseDown);
                C.get(0).onmousemove = onMouseMove
            }
            if (z.grid.clickable)$(overlay).click(onClick)
        }

        function findDataRanges() {
            E.datamin = D.datamin = 0;
            D.datamax = E.datamax = 1;
            if (u.length == 0)return;
            var i, found = false;
            for (i = 0; i < u.length; ++i) {
                if (u[i].data.length > 0) {
                    D.datamin = D.datamax = u[i].data[0][0];
                    E.datamin = E.datamax = u[i].data[0][1];
                    found = true;
                    break
                }
            }
            if (!found)return;
            for (i = 0; i < u.length; ++i) {
                var a = u[i].data;
                for (var j = 0; j < a.length; ++j) {
                    var x = a[j][0];
                    var y = a[j][1];
                    if (x < D.datamin)D.datamin = x; else if (x > D.datamax)D.datamax = x;
                    if (y < E.datamin)E.datamin = y; else if (y > E.datamax)E.datamax = y
                }
            }
        }

        function getTickSize(a, b, c, d) {
            var e = (c - b) / a;
            var f = getMagnitude(e);
            var g = e / f;
            var h = 1;
            if (g < 1.5)h = 1; else if (g < 2.25)h = 2; else if (g < 3)h = 2.5; else if (g < 7.5)h = 5; else h = 10;
            if (h == 2.5 && d == 0)h = 2;
            h *= f;
            return h
        }

        function calculateRange(a, b) {
            var c = b.min != null ? b.min : a.datamin;
            var d = b.max != null ? b.max : a.datamax;
            if (d - c == 0.0) {
                var e;
                if (d == 0.0)e = 1.0; else e = 0.01;
                c -= e;
                d += e
            }
            a.tickSize = getTickSize(b.noTicks, c, d, b.tickDecimals);
            var f;
            if (b.min == null) {
                f = b.autoscaleMargin;
                if (f != 0) {
                    c -= a.tickSize * f;
                    if (c < 0 && a.datamin >= 0)c = 0;
                    c = a.tickSize * Math.floor(c / a.tickSize)
                }
            }
            if (b.max == null) {
                f = b.autoscaleMargin;
                if (f != 0) {
                    d += a.tickSize * f;
                    if (d > 0 && a.datamax <= 0)d = 0;
                    d = a.tickSize * Math.ceil(d / a.tickSize)
                }
            }
            a.min = c;
            a.max = d
        }

        function extendXRangeIfNeededByBar() {
            if (z.xaxis.max == null) {
                var a = D.max;
                for (var i = 0; i < u.length; ++i)if (u[i].bars.show && u[i].bars.barWidth + D.datamax > a)a = D.max + u[i].bars.barWidth;
                D.max = a
            }
        }

        function defaultTickFormatter(a) {
            return "" + a
        }

        function calculateTicks(a, b) {
            var i;
            a.ticks = [];
            if (b.ticks) {
                var c = b.ticks;
                if ($.isFunction(c))c = c({min: a.min, max: a.max});
                for (i = 0; i < c.length; ++i) {
                    var v, label;
                    var t = c[i];
                    if (typeof(t) == "object") {
                        v = t[0];
                        if (t.length > 1)label = t[1]; else label = b.tickFormatter(v)
                    } else {
                        v = t;
                        label = b.tickFormatter(v)
                    }
                    a.ticks[i] = {v: v, label: label}
                }
            } else {
                var d = a.tickSize * Math.ceil(a.min / a.tickSize);
                for (i = 0; d + i * a.tickSize <= a.max; ++i) {
                    v = d + i * a.tickSize;
                    var e = b.tickDecimals;
                    if (e == null)e = 1 - Math.floor(Math.log(a.tickSize) / Math.LN10);
                    if (e < 0)e = 0;
                    v = v.toFixed(e);
                    a.ticks.push({v: v, label: b.tickFormatter(v)})
                }
            }
        }

        function calculateSpacing() {
            var i, max_label = "";
            for (i = 0; i < E.ticks.length; ++i) {
                var l = E.ticks[i].label.length;
                if (l > max_label.length)max_label = E.ticks[i].label
            }
            var a = $('<div style="position:absolute;top:-10000px;font-size:smaller" class="gridLabel">' + max_label + '</div>').appendTo(C);
            G = a.width();
            H = a.height();
            a.remove();
            var b = 2;
            if (z.points.show)b = Math.max(b, z.points.radius + z.points.lineWidth / 2);
            for (i = 0; i < u.length; ++i) {
                if (u[i].points.show)b = Math.max(b, u[i].points.radius + u[i].points.lineWidth / 2)
            }
            F.left = F.right = F.top = F.bottom = b;
            F.left += G + z.grid.labelMargin;
            F.bottom += H + z.grid.labelMargin;
            K = I - F.left - F.right;
            L = J - F.bottom - F.top;
            M = K / (D.max - D.min);
            N = L / (E.max - E.min)
        }

        function draw() {
            drawGrid();
            drawLabels();
            for (var i = 0; i < u.length; i++) {
                drawSeries(u[i])
            }
        }

        function tHoz(x) {
            return (x - D.min) * M
        }

        function tVert(y) {
            return L - (y - E.min) * N
        }

        function drawGrid() {
            B.save();
            B.translate(F.left, F.top);
            if (z.grid.backgroundColor != null) {
                B.fillStyle = z.grid.backgroundColor;
                B.fillRect(0, 0, K, L)
            }
            B.lineWidth = 1;
            B.strokeStyle = z.grid.tickColor;
            B.beginPath();
            var i, v;
            for (i = 0; i < D.ticks.length; ++i) {
                v = D.ticks[i].v;
                if (v == D.min || v == D.max)continue;
                B.moveTo(Math.floor(tHoz(v)) + B.lineWidth / 2, 0);
                B.lineTo(Math.floor(tHoz(v)) + B.lineWidth / 2, L)
            }
            for (i = 0; i < E.ticks.length; ++i) {
                v = E.ticks[i].v;
                if (v == E.min || v == E.max)continue;
                B.moveTo(0, Math.floor(tVert(v)) + B.lineWidth / 2);
                B.lineTo(K, Math.floor(tVert(v)) + B.lineWidth / 2)
            }
            B.stroke();
            B.lineWidth = 2;
            B.strokeStyle = z.grid.color;
            B.lineJoin = "round";
            B.strokeRect(0, 0, K, L);
            B.restore()
        }

        function drawLabels() {
            var i;
            var a;
            var b = '<div style="font-size:smaller;color:' + z.grid.color + '">';
            var c = 0;
            for (i = 0; i < D.ticks.length; ++i) {
                if (D.ticks[i].label) {
                    ++c
                }
            }
            var d = K / c;
            for (i = 0; i < D.ticks.length; ++i) {
                a = D.ticks[i];
                if (!a.label)continue;
                b += '<div style="position:absolute;top:' + (F.top + L + z.grid.labelMargin) + 'px;left:' + (F.left + tHoz(a.v) - d / 2) + 'px;width:' + d + 'px;text-align:center" class="gridLabel">' + a.label + "</div>"
            }
            for (i = 0; i < E.ticks.length; ++i) {
                a = E.ticks[i];
                if (!a.label || a.label.length == 0)continue;
                b += '<div style="position:absolute;top:' + (F.top + tVert(a.v) - H / 2) + 'px;left:0;width:' + G + 'px;text-align:right" class="gridLabel">' + a.label + "</div>"
            }
            b += '</div>';
            C.append(b)
        }

        function fillInSeriesOptions() {
            var i;
            var a = u.length;
            var b = [];
            var d = [];
            for (i = 0; i < u.length; ++i) {
                var e = u[i].color;
                if (e != null) {
                    --a;
                    if (typeof(e) == "number")d.push(e); else b.push(parseColor(u[i].color))
                }
            }
            for (i = 0; i < d.length; ++i) {
                a = Math.max(a, d[i] + 1)
            }
            var f = [];
            var g = 0;
            i = 0;
            while (f.length < a) {
                var c;
                if (z.colors.length == i)c = new Color(100, 100, 100); else c = parseColor(z.colors[i]);
                var h = g % 2 == 1 ? -1 : 1;
                var j = 1 + h * Math.ceil(g / 2) * 0.2;
                c.scale(j, j, j);
                f.push(c);
                ++i;
                if (i >= z.colors.length) {
                    i = 0;
                    ++g
                }
            }
            var k = 0;
            for (i = 0; i < u.length; ++i) {
                var s = u[i];
                if (s.color == null) {
                    s.color = f[k].toString();
                    ++k
                } else if (typeof(s.color) == "number")s.color = f[s.color].toString();
                s.lines = $.extend(true, {}, z.lines, s.lines);
                s.points = $.extend(true, {}, z.points, s.points);
                s.bars = $.extend(true, {}, z.bars, s.bars);
                if (s.shadowSize == null)s.shadowSize = z.shadowSize
            }
        }

        function drawSeries(a) {
            if (a.lines.show || (!a.bars.show && !a.points.show))drawSeriesLines(a);
            if (a.bars.show)drawSeriesBars(a);
            if (a.points.show)drawSeriesPoints(a)
        }

        function drawSeriesLines(g) {
            function plotLine(a, b) {
                if (a.length < 2)return;
                var c = tHoz(a[0][0]), prevy = tVert(a[0][1]) + b;
                B.beginPath();
                B.moveTo(c, prevy);
                for (var i = 0; i < a.length - 1; ++i) {
                    var d = a[i][0], y1 = a[i][1], x2 = a[i + 1][0], y2 = a[i + 1][1];
                    if (y1 <= y2 && y1 < E.min) {
                        if (y2 < E.min)continue;
                        d = (E.min - y1) / (y2 - y1) * (x2 - d) + d;
                        y1 = E.min
                    } else if (y2 <= y1 && y2 < E.min) {
                        if (y1 < E.min)continue;
                        x2 = (E.min - y1) / (y2 - y1) * (x2 - d) + d;
                        y2 = E.min
                    }
                    if (y1 >= y2 && y1 > E.max) {
                        if (y2 > E.max)continue;
                        d = (E.max - y1) / (y2 - y1) * (x2 - d) + d;
                        y1 = E.max
                    } else if (y2 >= y1 && y2 > E.max) {
                        if (y1 > E.max)continue;
                        x2 = (E.max - y1) / (y2 - y1) * (x2 - d) + d;
                        y2 = E.max
                    }
                    if (d <= x2 && d < D.min) {
                        if (x2 < D.min)continue;
                        y1 = (D.min - d) / (x2 - d) * (y2 - y1) + y1;
                        d = D.min
                    } else if (x2 <= d && x2 < D.min) {
                        if (d < D.min)continue;
                        y2 = (D.min - d) / (x2 - d) * (y2 - y1) + y1;
                        x2 = D.min
                    }
                    if (d >= x2 && d > D.max) {
                        if (x2 > D.max)continue;
                        y1 = (D.max - d) / (x2 - d) * (y2 - y1) + y1;
                        d = D.max
                    } else if (x2 >= d && x2 > D.max) {
                        if (d > D.max)continue;
                        y2 = (D.max - d) / (x2 - d) * (y2 - y1) + y1;
                        x2 = D.max
                    }
                    if (c != tHoz(d) || prevy != tVert(y1) + b)B.moveTo(tHoz(d), tVert(y1) + b);
                    c = tHoz(x2);
                    prevy = tVert(y2) + b;
                    B.lineTo(c, prevy)
                }
                B.stroke()
            }

            function plotLineArea(a) {
                if (a.length < 2)return;
                var b = Math.min(Math.max(0, E.min), E.max);
                var c, lastX = 0;
                var d = true;
                B.beginPath();
                for (var i = 0; i < a.length - 1; ++i) {
                    var e = a[i][0], y1 = a[i][1], x2 = a[i + 1][0], y2 = a[i + 1][1];
                    if (e <= x2 && e < D.min) {
                        if (x2 < D.min)continue;
                        y1 = (D.min - e) / (x2 - e) * (y2 - y1) + y1;
                        e = D.min
                    } else if (x2 <= e && x2 < D.min) {
                        if (e < D.min)continue;
                        y2 = (D.min - e) / (x2 - e) * (y2 - y1) + y1;
                        x2 = D.min
                    }
                    if (e >= x2 && e > D.max) {
                        if (x2 > D.max)continue;
                        y1 = (D.max - e) / (x2 - e) * (y2 - y1) + y1;
                        e = D.max
                    } else if (x2 >= e && x2 > D.max) {
                        if (e > D.max)continue;
                        y2 = (D.max - e) / (x2 - e) * (y2 - y1) + y1;
                        x2 = D.max
                    }
                    if (d) {
                        B.moveTo(tHoz(e), tVert(b));
                        d = false
                    }
                    if (y1 >= E.max && y2 >= E.max) {
                        B.lineTo(tHoz(e), tVert(E.max));
                        B.lineTo(tHoz(x2), tVert(E.max));
                        continue
                    } else if (y1 <= E.min && y2 <= E.min) {
                        B.lineTo(tHoz(e), tVert(E.min));
                        B.lineTo(tHoz(x2), tVert(E.min));
                        continue
                    }
                    var f = e, x2old = x2;
                    if (y1 <= y2 && y1 < E.min && y2 >= E.min) {
                        e = (E.min - y1) / (y2 - y1) * (x2 - e) + e;
                        y1 = E.min
                    } else if (y2 <= y1 && y2 < E.min && y1 >= E.min) {
                        x2 = (E.min - y1) / (y2 - y1) * (x2 - e) + e;
                        y2 = E.min
                    }
                    if (y1 >= y2 && y1 > E.max && y2 <= E.max) {
                        e = (E.max - y1) / (y2 - y1) * (x2 - e) + e;
                        y1 = E.max
                    } else if (y2 >= y1 && y2 > E.max && y1 <= E.max) {
                        x2 = (E.max - y1) / (y2 - y1) * (x2 - e) + e;
                        y2 = E.max
                    }
                    if (e != f) {
                        if (y1 <= E.min)c = E.min; else c = E.max;
                        B.lineTo(tHoz(f), tVert(c));
                        B.lineTo(tHoz(e), tVert(c))
                    }
                    B.lineTo(tHoz(e), tVert(y1));
                    B.lineTo(tHoz(x2), tVert(y2));
                    if (x2 != x2old) {
                        if (y2 <= E.min)c = E.min; else c = E.max;
                        B.lineTo(tHoz(x2old), tVert(c));
                        B.lineTo(tHoz(x2), tVert(c))
                    }
                    lastX = Math.max(x2, x2old)
                }
                B.lineTo(tHoz(lastX), tVert(b));
                B.fill()
            }

            B.save();
            B.translate(F.left, F.top);
            B.lineJoin = "round";
            var h = g.lines.lineWidth;
            var j = g.shadowSize;
            if (j > 0) {
                B.lineWidth = j / 2;
                B.strokeStyle = "rgba(0,0,0,0.1)";
                plotLine(g.data, h / 2 + j / 2 + B.lineWidth / 2);
                B.lineWidth = j / 2;
                B.strokeStyle = "rgba(0,0,0,0.2)";
                plotLine(g.data, h / 2 + B.lineWidth / 2)
            }
            B.lineWidth = h;
            B.strokeStyle = g.color;
            if (g.lines.fill) {
                B.fillStyle = g.lines.fillColor != null ? g.lines.fillColor : parseColor(g.color).scale(null, null, null, 0.4).toString();
                plotLineArea(g.data, 0)
            }
            plotLine(g.data, 0);
            B.restore()
        }

        function drawSeriesPoints(d) {
            function plotPoints(a, b, c) {
                for (var i = 0; i < a.length; ++i) {
                    var x = a[i][0], y = a[i][1];
                    if (x < D.min || x > D.max || y < E.min || y > E.max)continue;
                    B.beginPath();
                    B.arc(tHoz(x), tVert(y), b, 0, 2 * Math.PI, true);
                    if (c)B.fill();
                    B.stroke()
                }
            }

            function plotPointShadows(a, b, c) {
                for (var i = 0; i < a.length; ++i) {
                    var x = a[i][0], y = a[i][1];
                    if (x < D.min || x > D.max || y < E.min || y > E.max)continue;
                    B.beginPath();
                    B.arc(tHoz(x), tVert(y) + b, c, 0, Math.PI, false);
                    B.stroke()
                }
            }

            B.save();
            B.translate(F.left, F.top);
            var e = d.lines.lineWidth;
            var f = d.shadowSize;
            if (f > 0) {
                B.lineWidth = f / 2;
                B.strokeStyle = "rgba(0,0,0,0.1)";
                plotPointShadows(d.data, f / 2 + B.lineWidth / 2, d.points.radius);
                B.lineWidth = f / 2;
                B.strokeStyle = "rgba(0,0,0,0.2)";
                plotPointShadows(d.data, B.lineWidth / 2, d.points.radius)
            }
            B.lineWidth = d.points.lineWidth;
            B.strokeStyle = d.color;
            B.fillStyle = d.points.fillColor != null ? d.points.fillColor : d.color;
            plotPoints(d.data, d.points.radius, d.points.fill);
            B.restore()
        }

        function drawSeriesBars(g) {
            function plotBars(a, b, c, d) {
                if (a.length < 2)return;
                for (var i = 0; i < a.length; i++) {
                    var x = a[i][0], y = a[i][1];
                    var e = true, drawTop = true, drawRight = true;
                    var f = x, right = x + b, bottom = 0, top = y;
                    if (right < D.min || f > D.max || top < E.min || bottom > E.max)continue;
                    if (f < D.min) {
                        f = D.min;
                        e = false
                    }
                    if (right > D.max) {
                        right = D.max;
                        drawRight = false
                    }
                    if (bottom < E.min)bottom = E.min;
                    if (top > E.max) {
                        top = E.max;
                        drawTop = false
                    }
                    if (d) {
                        B.beginPath();
                        B.moveTo(tHoz(f), tVert(bottom) + c);
                        B.lineTo(tHoz(f), tVert(top) + c);
                        B.lineTo(tHoz(right), tVert(top) + c);
                        B.lineTo(tHoz(right), tVert(bottom) + c);
                        B.fill()
                    }
                    if (e || drawRight || drawTop) {
                        B.beginPath();
                        B.moveTo(tHoz(f), tVert(bottom) + c);
                        if (e)B.lineTo(tHoz(f), tVert(top) + c); else B.moveTo(tHoz(f), tVert(top) + c);
                        if (drawTop)B.lineTo(tHoz(right), tVert(top) + c); else B.moveTo(tHoz(right), tVert(top) + c);
                        if (drawRight)B.lineTo(tHoz(right), tVert(bottom) + c); else B.moveTo(tHoz(right), tVert(bottom) + c);
                        B.stroke()
                    }
                }
            }

            B.save();
            B.translate(F.left, F.top);
            B.lineJoin = "round";
            var h = g.bars.barWidth;
            var j = Math.min(g.bars.lineWidth, h);
            B.lineWidth = j;
            B.strokeStyle = g.color;
            if (g.bars.fill) {
                B.fillStyle = g.bars.fillColor != null ? g.bars.fillColor : parseColor(g.color).scale(null, null, null, 0.4).toString()
            }
            plotBars(g.data, h, 0, g.bars.fill);
            B.restore()
        }

        function insertLegend() {
            if (!z.legend.show)return;
            var a = [];
            var b = false;
            for (i = 0; i < u.length; ++i) {
                if (!u[i].label)continue;
                if (i % z.legend.noColumns == 0) {
                    if (b)a.push('</tr>');
                    a.push('<tr>');
                    b = true
                }
                var d = u[i].label;
                if (z.legend.labelFormatter != null)d = z.legend.labelFormatter(d);
                a.push('<td class="legendColorBox"><div style="border:1px solid ' + z.legend.labelBoxBorderColor + ';padding:1px"><div style="width:14px;height:10px;background-color:' + u[i].color + '"></div></div></td>' + '<td class="legendLabel">' + d + '</td>')
            }
            if (b)a.push('</tr>');
            if (a.length > 0) {
                var e = '<table style="font-size:smaller;color:' + z.grid.color + '">' + a.join("") + '</table>';
                if (z.legend.container != null)z.legend.container.append(e); else {
                    var f = "";
                    var p = z.legend.position, m = z.legend.margin;
                    if (p.charAt(0) == "n")f += 'top:' + (m + F.top) + 'px;'; else if (p.charAt(0) == "s")f += 'bottom:' + (m + F.bottom) + 'px;';
                    if (p.charAt(1) == "e")f += 'right:' + (m + F.right) + 'px;'; else if (p.charAt(1) == "w")f += 'left:' + (m + F.bottom) + 'px;';
                    var g = $('<div class="legend" style="position:absolute;z-index:2;' + f + '">' + e + '</div>').appendTo(C);
                    if (z.legend.backgroundOpacity != 0.0) {
                        var c = z.legend.backgroundColor;
                        if (c == null) {
                            var h;
                            if (z.grid.backgroundColor != null)h = z.grid.backgroundColor; else h = extractColor(g);
                            c = parseColor(h).adjust(null, null, null, 1).toString()
                        }
                        $('<div style="position:absolute;width:' + g.width() + 'px;height:' + g.height() + 'px;' + f + 'background-color:' + c + ';"> </div>').appendTo(C).css('opacity', z.legend.backgroundOpacity)
                    }
                }
            }
        }

        var O = {pageX: null, pageY: null};
        var P = {first: {x: -1, y: -1}, second: {x: -1, y: -1}};
        var Q = null;
        var R = null;
        var S = false;

        function onMouseMove(a) {
            var e = a || window.event;
            if (e.pageX == null && e.clientX != null) {
                var c = document.documentElement, b = document.body;
                O.pageX = e.clientX + (c && c.scrollLeft || b.scrollLeft || 0);
                O.pageY = e.clientY + (c && c.scrollTop || b.scrollTop || 0)
            } else {
                O.pageX = e.pageX;
                O.pageY = e.pageY
            }
        }

        function onMouseDown(e) {
            if (e.which != 1)return;
            setSelectionPos(P.first, e);
            if (R != null)clearInterval(R);
            O.pageX = null;
            R = setInterval(updateSelectionOnMouseMove, 200);
            $(document).one("mouseup", onSelectionMouseUp)
        }

        function onClick(e) {
            if (S) {
                S = false;
                return
            }
            var a = $(overlay).offset();
            var b = {};
            b.x = e.pageX - a.left - F.left;
            b.x = D.min + b.x / M;
            b.y = e.pageY - a.top - F.top;
            b.y = E.max - b.y / N;
            C.trigger("plotclick", [b])
        }

        function triggerSelectedEvent() {
            var a, x2, y1, y2;
            if (P.first.x <= P.second.x) {
                a = P.first.x;
                x2 = P.second.x
            } else {
                a = P.second.x;
                x2 = P.first.x
            }
            if (P.first.y >= P.second.y) {
                y1 = P.first.y;
                y2 = P.second.y
            } else {
                y1 = P.second.y;
                y2 = P.first.y
            }
            a = D.min + a / M;
            x2 = D.min + x2 / M;
            y1 = E.max - y1 / N;
            y2 = E.max - y2 / N;
            C.trigger("selected", [{x1: a, y1: y1, x2: x2, y2: y2}])
        }

        function onSelectionMouseUp(e) {
            if (R != null) {
                clearInterval(R);
                R = null
            }
            setSelectionPos(P.second, e);
            clearSelection();
            if (!selectionIsSane() || e.which != 1)return false;
            drawSelection();
            triggerSelectedEvent();
            S = true;
            return false
        }

        function setSelectionPos(a, e) {
            var b = $(overlay).offset();
            if (z.selection.mode == "y") {
                if (a == P.first)a.x = 0; else a.x = K
            } else {
                a.x = e.pageX - b.left - F.left;
                a.x = Math.min(Math.max(0, a.x), K)
            }
            if (z.selection.mode == "x") {
                if (a == P.first)a.y = 0; else a.y = L
            } else {
                a.y = e.pageY - b.top - F.top;
                a.y = Math.min(Math.max(0, a.y), L)
            }
        }

        function updateSelectionOnMouseMove() {
            if (O.pageX == null)return;
            setSelectionPos(P.second, O);
            clearSelection();
            if (selectionIsSane())drawSelection()
        }

        function clearSelection() {
            if (Q == null)return;
            var x = Math.min(Q.first.x, Q.second.x), y = Math.min(Q.first.y, Q.second.y), w = Math.abs(Q.second.x - Q.first.x), h = Math.abs(Q.second.y - Q.first.y);
            octx.clearRect(x + F.left - octx.lineWidth, y + F.top - octx.lineWidth, w + octx.lineWidth * 2, h + octx.lineWidth * 2);
            Q = null
        }

        function setSelection(a) {
            clearSelection();
            if (z.selection.mode == "x") {
                P.first.y = 0;
                P.second.y = L
            } else {
                P.first.y = (E.max - a.y1) * N;
                P.second.y = (E.max - a.y2) * N
            }
            if (z.selection.mode == "y") {
                P.first.x = 0;
                P.second.x = K
            } else {
                P.first.x = (a.x1 - D.min) * M;
                P.second.x = (a.x2 - D.min) * M
            }
            drawSelection();
            triggerSelectedEvent()
        }

        function drawSelection() {
            if (Q != null && P.first.x == Q.first.x && P.first.y == Q.first.y && P.second.x == Q.second.x && P.second.y == Q.second.y)return;
            octx.strokeStyle = parseColor(z.selection.color).scale(null, null, null, 0.8).toString();
            octx.lineWidth = 1;
            B.lineJoin = "round";
            octx.fillStyle = parseColor(z.selection.color).scale(null, null, null, 0.4).toString();
            Q = {first: {x: P.first.x, y: P.first.y}, second: {x: P.second.x, y: P.second.y}};
            var x = Math.min(P.first.x, P.second.x), y = Math.min(P.first.y, P.second.y), w = Math.abs(P.second.x - P.first.x), h = Math.abs(P.second.y - P.first.y);
            octx.fillRect(x + F.left, y + F.top, w, h);
            octx.strokeRect(x + F.left, y + F.top, w, h)
        }

        function selectionIsSane() {
            var a = 5;
            return Math.abs(P.second.x - P.first.x) >= a && Math.abs(P.second.y - P.first.y) >= a
        }
    }

    $.plot = function (a, b, c) {
        var d = new Plot(a, b, c);
        return d
    };
    function getMagnitude(x) {
        return Math.pow(10, Math.floor(Math.log(x) / Math.LN10))
    }

    function Color(r, g, b, a) {
        var e = ['r', 'g', 'b', 'a'];
        var x = 4;
        while (-1 < --x) {
            this[e[x]] = arguments[x] || ((x == 3) ? 1.0 : 0)
        }
        this.toString = function () {
            if (this.a >= 1.0) {
                return "rgb(" + [this.r, this.g, this.b].join(",") + ")"
            } else {
                return "rgba(" + [this.r, this.g, this.b, this.a].join(",") + ")"
            }
        };
        this.scale = function (a, b, c, d) {
            x = 4;
            while (-1 < --x) {
                if (arguments[x] != null)this[e[x]] *= arguments[x]
            }
            return this.normalize()
        };
        this.adjust = function (a, b, c, d) {
            x = 4;
            while (-1 < --x) {
                if (arguments[x] != null)this[e[x]] += arguments[x]
            }
            return this.normalize()
        };
        this.clone = function () {
            return new Color(this.r, this.b, this.g, this.a)
        };
        var f = function (a, b, c) {
            return Math.max(Math.min(a, c), b)
        };
        this.normalize = function () {
            this.r = f(parseInt(this.r), 0, 255);
            this.g = f(parseInt(this.g), 0, 255);
            this.b = f(parseInt(this.b), 0, 255);
            this.a = f(this.a, 0, 1);
            return this
        };
        this.normalize()
    }

    var T = {
        aqua: [0, 255, 255],
        azure: [240, 255, 255],
        beige: [245, 245, 220],
        black: [0, 0, 0],
        blue: [0, 0, 255],
        brown: [165, 42, 42],
        cyan: [0, 255, 255],
        darkblue: [0, 0, 139],
        darkcyan: [0, 139, 139],
        darkgrey: [169, 169, 169],
        darkgreen: [0, 100, 0],
        darkkhaki: [189, 183, 107],
        darkmagenta: [139, 0, 139],
        darkolivegreen: [85, 107, 47],
        darkorange: [255, 140, 0],
        darkorchid: [153, 50, 204],
        darkred: [139, 0, 0],
        darksalmon: [233, 150, 122],
        darkviolet: [148, 0, 211],
        fuchsia: [255, 0, 255],
        gold: [255, 215, 0],
        green: [0, 128, 0],
        indigo: [75, 0, 130],
        khaki: [240, 230, 140],
        lightblue: [173, 216, 230],
        lightcyan: [224, 255, 255],
        lightgreen: [144, 238, 144],
        lightgrey: [211, 211, 211],
        lightpink: [255, 182, 193],
        lightyellow: [255, 255, 224],
        lime: [0, 255, 0],
        magenta: [255, 0, 255],
        maroon: [128, 0, 0],
        navy: [0, 0, 128],
        olive: [128, 128, 0],
        orange: [255, 165, 0],
        pink: [255, 192, 203],
        purple: [128, 0, 128],
        violet: [128, 0, 128],
        red: [255, 0, 0],
        silver: [192, 192, 192],
        white: [255, 255, 255],
        yellow: [255, 255, 0]
    };

    function extractColor(a) {
        var b, elem = a;
        do {
            b = elem.css("background-color").toLowerCase();
            if (b != '' && b != 'transparent')break;
            elem = elem.parent()
        } while (!$.nodeName(elem.get(0), "body"));
        if (b == "rgba(0, 0, 0, 0)")return "transparent";
        return b
    }

    function parseColor(a) {
        var b;
        if (b = /rgb\(\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*\)/.exec(a))return new Color(parseInt(b[1]), parseInt(b[2]), parseInt(b[3]));
        if (b = /rgba\(\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9]+(?:\.[0-9]+)?)\s*\)/.exec(a))return new Color(parseInt(b[1]), parseInt(b[2]), parseInt(b[3]), parseFloat(b[4]));
        if (b = /rgb\(\s*([0-9]+(?:\.[0-9]+)?)\%\s*,\s*([0-9]+(?:\.[0-9]+)?)\%\s*,\s*([0-9]+(?:\.[0-9]+)?)\%\s*\)/.exec(a))return new Color(parseFloat(b[1]) * 2.55, parseFloat(b[2]) * 2.55, parseFloat(b[3]) * 2.55);
        if (b = /rgba\(\s*([0-9]+(?:\.[0-9]+)?)\%\s*,\s*([0-9]+(?:\.[0-9]+)?)\%\s*,\s*([0-9]+(?:\.[0-9]+)?)\%\s*,\s*([0-9]+(?:\.[0-9]+)?)\s*\)/.exec(a))return new Color(parseFloat(b[1]) * 2.55, parseFloat(b[2]) * 2.55, parseFloat(b[3]) * 2.55, parseFloat(b[4]));
        if (b = /#([a-fA-F0-9]{2})([a-fA-F0-9]{2})([a-fA-F0-9]{2})/.exec(a))return new Color(parseInt(b[1], 16), parseInt(b[2], 16), parseInt(b[3], 16));
        if (b = /#([a-fA-F0-9])([a-fA-F0-9])([a-fA-F0-9])/.exec(a))return new Color(parseInt(b[1] + b[1], 16), parseInt(b[2] + b[2], 16), parseInt(b[3] + b[3], 16));
        var c = jQuery.trim(a).toLowerCase();
        if (c == "transparent")return new Color(255, 255, 255, 0); else {
            b = T[c];
            return new Color(b[0], b[1], b[2])
        }
    }
})(jQuery);