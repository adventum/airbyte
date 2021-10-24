/*
 * Copyright (c) 2021 Airbyte, Inc., all rights reserved.
 */

package io.airbyte.integrations.destination.pulsar;

import com.fasterxml.jackson.databind.JsonNode;
import com.google.common.collect.ImmutableMap;
import io.airbyte.commons.json.Jsons;
import io.airbyte.integrations.base.AirbyteStreamNameNamespacePair;
import io.airbyte.integrations.base.FailureTrackingAirbyteMessageConsumer;
import io.airbyte.integrations.destination.NamingConventionTransformer;
import io.airbyte.protocol.models.AirbyteMessage;
import io.airbyte.protocol.models.AirbyteRecordMessage;
import io.airbyte.protocol.models.ConfiguredAirbyteCatalog;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.function.Consumer;
import java.util.function.Function;
import java.util.stream.Collectors;
import io.airbyte.commons.lang.Exceptions;
import org.apache.pulsar.client.api.Producer;
import org.apache.pulsar.client.api.PulsarClientException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PulsarRecordConsumer extends FailureTrackingAirbyteMessageConsumer {

  private static final Logger LOGGER = LoggerFactory.getLogger(PulsarRecordConsumer.class);

  private final PulsarDestinationConfig config;
  private final Map<AirbyteStreamNameNamespacePair, Producer<JsonNode>> producerMap;
  private final ConfiguredAirbyteCatalog catalog;
  private final Consumer<AirbyteMessage> outputRecordCollector;
  private final NamingConventionTransformer nameTransformer;

  private AirbyteMessage lastStateMessage = null;

  public PulsarRecordConsumer(final PulsarDestinationConfig pulsarDestinationConfig,
                             final ConfiguredAirbyteCatalog catalog,
                             final Consumer<AirbyteMessage> outputRecordCollector,
                             final NamingConventionTransformer nameTransformer) {
    this.config = pulsarDestinationConfig;
    this.producerMap = new HashMap<>();
    this.catalog = catalog;
    this.outputRecordCollector = outputRecordCollector;
    this.nameTransformer = nameTransformer;
  }

  @Override
  protected void startTracked() {
    producerMap.putAll(buildProducerMap());
  }

  @Override
  protected void acceptTracked(final AirbyteMessage airbyteMessage) {
    if (airbyteMessage.getType() == AirbyteMessage.Type.STATE) {
      lastStateMessage = airbyteMessage;
    } else if (airbyteMessage.getType() == AirbyteMessage.Type.RECORD) {
      final AirbyteRecordMessage recordMessage = airbyteMessage.getRecord();
      final Producer<JsonNode> producer = producerMap.get(AirbyteStreamNameNamespacePair.fromRecordMessage(recordMessage));
      final String key = UUID.randomUUID().toString();
      final JsonNode value = Jsons.jsonNode(ImmutableMap.of(
          PulsarDestination.COLUMN_NAME_AB_ID, key,
          PulsarDestination.COLUMN_NAME_STREAM, recordMessage.getStream(),
          PulsarDestination.COLUMN_NAME_EMITTED_AT, recordMessage.getEmittedAt(),
          PulsarDestination.COLUMN_NAME_DATA, recordMessage.getData()));

      sendRecord(producer, value);
    } else {
      LOGGER.warn("Unexpected message: " + airbyteMessage.getType());
    }
  }

  Map<AirbyteStreamNameNamespacePair, Producer<JsonNode>> buildProducerMap() {
    return catalog.getStreams().stream()
        .map(stream -> AirbyteStreamNameNamespacePair.fromAirbyteSteam(stream.getStream()))
        .collect(Collectors.toMap(Function.identity(), pair -> {
          String topic = nameTransformer.getIdentifier(config.getTopicPattern()
                .replaceAll("\\{namespace}", Optional.ofNullable(pair.getNamespace()).orElse(""))
                .replaceAll("\\{stream}", Optional.ofNullable(pair.getName()).orElse("")));
          return config.getProducer(topic);
        }));
  }

  private void sendRecord(final Producer<JsonNode> producer, final JsonNode record) {
    producer.sendAsync(record);
    if (config.isSync()) {
      try {
        producer.flush();
      } catch (PulsarClientException e) {
        LOGGER.error("Error sending message to topic.", e);
        throw new RuntimeException("Cannot send message to Pulsar. Error: " + e.getMessage(), e);
      }
      outputRecordCollector.accept(lastStateMessage);
    }
  }

  @Override
  protected void close(final boolean hasFailed) {
    producerMap.values().forEach(producer -> {
      Exceptions.swallow(producer::flush);
      Exceptions.swallow(producer::close);
    });
    outputRecordCollector.accept(lastStateMessage);
  }

}
