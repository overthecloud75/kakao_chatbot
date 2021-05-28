from tensorflow.keras.models import Model
from tensorflow.keras.layers import Embedding, Dropout, Conv1D, GlobalMaxPooling1D, Dense, Input, Flatten, Concatenate

class IntentModel:
    def __init__(self, max_len=22, vocab_size=400, filter_sizes=[2,3,5], embedding_dim=16, num_filters=32, drop=0.5, len_label=70):
        self.max_len=max_len
        self.vocab_size = vocab_size
        self.filter_sizes = filter_sizes
        self.embedding_dim = embedding_dim
        self.num_filters = num_filters
        self.drop = drop
        self.len_label=len_label

    def create_model(self):
        model_input = Input(shape=(self.max_len,))
        z = Embedding(self.vocab_size, self.embedding_dim, input_length=self.max_len)(model_input)

        conv_blocks = []

        for sz in self.filter_sizes:
            conv = Conv1D(filters=self.num_filters,
                          kernel_size=sz,
                          padding="valid",
                          activation="relu",
                          strides=1)(z)
            conv = GlobalMaxPooling1D()(conv)
            conv = Flatten()(conv)
            conv_blocks.append(conv)

        z = Concatenate()(conv_blocks) if len(conv_blocks) > 1 else conv_blocks[0]
        z = Dropout(self.drop)(z)
        model_output = Dense(self.len_label, activation='softmax')(z)

        model = Model(model_input, model_output)
        model.summary()

        model.compile(loss='categorical_crossentropy',
                      optimizer='adam',
                      metrics=['acc'])
        return model

