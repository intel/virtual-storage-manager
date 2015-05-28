define(function (require) {
    var Base = require('zrender/shape/Base');
    var smoothBezier = require('zrender/shape/util/smoothBezier');
    var zrUtil = require('zrender/tool/util');
    
    function HalfSmoothPolygon(options) {
        Base.call(this, options);
    }

    HalfSmoothPolygon.prototype = {
        type : 'half-smooth-polygon',
        buildPath : function (ctx, style) {
            var pointList = style.pointList;
            if (pointList.length < 2) {
                return;
            }
            if (style.smooth) {
                var controlPoints = smoothBezier(
                    pointList.slice(0, -2), style.smooth, false, style.smoothConstraint
                );

                ctx.moveTo(pointList[0][0], pointList[0][1]);
                var cp1;
                var cp2;
                var p;
                var l = pointList.length;
                for (var i = 0; i < l - 3; i++) {
                    cp1 = controlPoints[i * 2];
                    cp2 = controlPoints[i * 2 + 1];
                    p = pointList[i + 1];
                    ctx.bezierCurveTo(
                        cp1[0], cp1[1], cp2[0], cp2[1], p[0], p[1]
                    );
                }
                ctx.lineTo(pointList[l - 2][0], pointList[l - 2][1]);
                ctx.lineTo(pointList[l - 1][0], pointList[l - 1][1]);
                ctx.lineTo(pointList[0][0], pointList[0][1]);
            } 
            else {
                require('zrender/shape/Polygon').prototype.buildPath(
                    ctx, style
                );
            }
            return;
        }
    };

    zrUtil.inherits(HalfSmoothPolygon, Base);
    
    return HalfSmoothPolygon;
});