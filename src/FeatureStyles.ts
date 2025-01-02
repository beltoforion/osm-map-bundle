import { Circle as CircleStyle, Fill, Stroke, Style, Text } from 'ol/style';

export interface FeatureStyle {
    getStyle(): Style;
}

export type FeatureStyleDictionary = { [key: string]: FeatureStyle };

export class LineStyle implements FeatureStyle {
    private caption: string;
    private color: string;
    private width: number;

    constructor(caption: string, color: string, width: number) {
        this.caption = caption;
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
    private caption: string;
    private color: string;

    constructor(caption: string, color: string) {
        this.caption = caption;
        this.color = color;
    }

    public getStyle(): Style {
        return new Style({
            image: new CircleStyle({
                fill: new Fill({ color: this.color }),
                radius: 8,
                stroke: new Stroke({ color: '#ff0', width: 1 })
            }),
            text: new Text({
                text: this.caption,
                scale: 1.3,
                offsetX: 0,
                offsetY: 20,
                fill: new Fill({ color: '#000000' }),
                stroke: new Stroke({ color: this.color, width: 3.5 })
            })
        })
    }
}