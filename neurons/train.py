# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# Copyright © 2023 const

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import os
import torch
import argparse
import pretrain
import bittensor as bt

# === Config ===
def get_config():
    parser = argparse.ArgumentParser()
    parser.add_argument( "--model_path", type=str, required=False, help="Override model path")
    parser.add_argument( "--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu", help="Device name.")
    bt.wallet.add_args( parser )
    bt.logging.add_args( parser )
    config = bt.config(parser)
    config.full_path = os.path.expanduser(
        "{}/{}/{}/netuid{}/{}".format(
            config.logging.logging_dir,
            config.wallet.name,
            config.wallet.hotkey,
            pretrain.NETUID,
            "miner",
        )
    )
    if config.model_path == None:
        config.model_path = config.full_path + '/' + 'model.pth'
    if not os.path.exists( config.model_path ):
        os.makedirs( config.model_path, exist_ok=True )
    return config
config = get_config()
print (config)

model = pretrain.model.get_model()
model.zero_grad()
model.train()
model.to( config.device )

optimizer = torch.optim.AdamW( model.parameters(), lr=0.000001, weight_decay=0.01 )
loader = pretrain.dataset.SubsetFalconLoader( batch_size=3, sequence_length=512, pages=[1] )

num_epochs = 5 
for epoch in range(num_epochs):
    for i, batch in enumerate(loader):
        inputs = batch.to( model.device )
        outputs = model( inputs, labels=inputs )
        outputs.loss.backward()
        torch.cuda.empty_cache()
        optimizer.step()
        bt.logging.success( f'Acc: step: {i} loss: {outputs.loss}' )

bt.logging.success( f'Saving model to {config.model_path}' )
torch.save( model.state_dict(), config.model_path )