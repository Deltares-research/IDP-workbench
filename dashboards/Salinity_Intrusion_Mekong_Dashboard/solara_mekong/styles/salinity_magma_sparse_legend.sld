<?xml version="1.0" encoding="UTF-8"?>
<!--
  Absolute salinity style matching the salinity_increase legend trick:
  first ColorMapEntry labels are the title lines in GetLegendGraphic
  (GeoServer does NOT use <Title>/<Abstract> for that raster colorbar header).

  Paste into GeoServer style "salinity" → Validate → Submit
-->
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld"
  xmlns:sld="http://www.opengis.net/sld"
  xmlns:ogc="http://www.opengis.net/ogc"
  xmlns:gml="http://www.opengis.net/gml"
  version="1.0.0">
  <NamedLayer>
    <Name>salinity</Name>
    <UserStyle>
      <Name>salinity</Name>
      <Title>Salinity</Title>
      <FeatureTypeStyle>
        <Rule>
          <RasterSymbolizer>
            <ChannelSelection>
              <GrayChannel>
                <SourceChannelName>1</SourceChannelName>
              </GrayChannel>
            </ChannelSelection>
            <ColorMap type="ramp">
              <!-- Legend header rows (same hack as salinity_increase) -->
              <ColorMapEntry color="#000004" quantity="0" opacity="0.01" label="Salinity"/>
              <ColorMapEntry color="#000004" quantity="0" opacity="0.01" label="(PSU)"/>
              <ColorMapEntry color="#000004" quantity="0" opacity="0.01" label="0"/>
              <ColorMapEntry color="#29115a" quantity="5" label="5"/>
              <ColorMapEntry color="#6a1c81" quantity="10" label="10"/>
              <ColorMapEntry color="#aa337d" quantity="15" label="15"/>
              <ColorMapEntry color="#d9466b" quantity="20" label="20"/>
              <ColorMapEntry color="#f7725c" quantity="25" label="25"/>
              <ColorMapEntry color="#febd82" quantity="30" label="30"/>
              <ColorMapEntry color="#fcfdbf" quantity="35" label="35"/>
            </ColorMap>
          </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>
