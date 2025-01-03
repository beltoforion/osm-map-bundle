import { Circle as CircleStyle, Fill, Stroke, Style, Text } from 'ol/style';

export interface FeatureStyle {
    getStyle(): Style;
}

export type FeatureStyleDictionary = { [key: string]: FeatureStyle };

export class LineStyle implements FeatureStyle {
    private color: string;
    private width: number;

    constructor(color: string, width: number) {
        this.color = color;
        this.width = width;
    }

    public getStyle(): Style {
        return new Style({
            stroke: new Stroke({
                color: this.color,
                width: this.width
            })
        });
    }
}

export class AnnotatedPointStyle implements FeatureStyle {
    private foreground: string;
    private background: string;
    private strokeWidth: number;
    private radius: number;

    constructor(foreground: string, background: string = '#000', radius : number = 8, strokeWidth: number = 1) {
        this.foreground = foreground;
        this.background = background;
        this.strokeWidth = strokeWidth;
        this.radius = radius;
    }

    public getStyle(): Style {
        return new Style({
            image: new CircleStyle({
                fill: new Fill({ color: this.foreground }),
                radius: this.radius,
                stroke: new Stroke({ color: this.background, width: this.strokeWidth })
            }),
            text: new Text({
                text: '',
                scale: 1.3,
                offsetX: 0,
                offsetY: 20,
                fill: new Fill({ color: this.background }),
                stroke: new Stroke({ color: this.foreground, width: this.strokeWidth })
            })
        })
    }
}