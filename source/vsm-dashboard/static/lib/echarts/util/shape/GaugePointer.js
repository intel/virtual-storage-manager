define(function (require) {
    var Base = require('zrender/shape/Base');
    var zrUtil = require('zrender/tool/util');

    function GaugePointer(options) {
        Base.call(this, options);
    }

    GaugePointer.prototype =  {
        type: 'gauge-pointer',
        buildPath : function (ctx, style) {
            var r = style.r;
            var width = style.width;
            var angle = style.angle;
            var x = style.x - Math.cos(angle) * width * (width >= r / 3 ? 1 : 2);
            var y = style.y + Math.sin(angle) * width * (width >= r / 3 ? 1 : 2);

            angle = style.angle - Math.PI / 2;
            ctx.moveTo(x, y);
            ctx.lineTo(
                style.x + Math.cos(angle) * width,
                style.y - Math.sin(angle) * width
            );
            ctx.lineTo(
                style.x + Math.cos(style.angle) * r,
                style.y - Math.sin(style.angle) * r
            );
            ctx.lineTo(
                style.x - Math.cos(angle) * width,
                style.y + Math.sin(angle) * width
            );
            ctx.lineTo(x, y);
            return;
        },

        getRect : function(style) {
            if (style.__rect) {
                return style.__rect;
            }

            var width = style.width * 2;
            var xStart = style.x;
            var yStart = style.y;
            var xEnd = xStart + Math.cos(style.angle) * style.r;
            var yEnd = yStart - Math.sin(style.angle) * style.r;

            style.__rect = {
                x : Math.min(xStart, xEnd) - width,
                y : Math.min(yStart, yEnd) - width,
                width : Math.abs(xStart - xEnd) + width,
                height : Math.abs(yStart - yEnd) + width
            };
            return style.__rect;
        },

        isCover : require('./normalIsCover')
    };

    zrUtil.inherits(GaugePointer, Base);

    return GaugePointer;
});
