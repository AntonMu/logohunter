import cv2
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from utils import chunks, bbox_colors, draw_annotated_box
from timeit import default_timer as timer
from PIL import Image


def features_from_image(img_array, model, preprocess, batch_size = 100):
    """
    Extract features from image array given a decapitated keras model.
    Use a generator to avoid running out of memory for large inputs.

    Args:
      img_array: (N, H, W, C) list/array of input images
      model: keras model, outputs
    Returns:
      (N, F) array of 1D features
    """
    
    if len(img_array) == 0:
        return np.array([])

    steps = len(img_array)//batch_size + 1
    img_gen = chunks(img_array, batch_size, preprocessing_function = preprocess)
    features = model.predict_generator(img_gen, steps = steps)

    # if the generator has looped past end of array, cut it down
    features = features[:len(img_array)]

    # reshape features: flatten last three dimensions to one
    features = features.reshape(features.shape[0], np.prod(features.shape[1:]))
    return features

def similarity_cutoff(feat_input, features, threshold=0.95):
    """
    Given list of input feature and feature database, compute distribution of
    cosine similarityof the database with respect to each input. Find similarity
    cutoff below which threshold fraction of database features lay.

    Args:
      feat_input: (n_input, N) array of features for input
      features: (n_database, N) array of features for logo database
      threshold: fractional threshold
    Returns:
      cutoff_list: list of cutoffs for each input
    """

    start = timer()
    cs = cosine_similarity(X = feat_input, Y = features)
    cutoff_list = []
    # assume only one input? otherwise list
    for i, cs1 in enumerate(cs):
        hist, bins = np.histogram(cs1, bins=np.arange(0,1,0.001))
        cutoff = bins[np.where(np.cumsum(hist)< threshold*len(cs1))][-1]
        cutoff_list.append(cutoff)
    end = timer()
    print('Computed similarity cutoffs given inputs {:.2f}'.format(end - start))

    return cutoff_list

def similar_matches(feat_input, features_cand, cutoff_list):
    """
    Given features of inputs to check candidates against, compute cosine
    similarity and define a match if cosine similarity is above a cutoff.

    Args:
      feat_input:    (n_input, N) array of features for input
      features_cand: (n_candidates, N) array of features for candidates

    Returns:
      matches: (n_input, ) list of indices (each running from 0 to n_candidates)
        where a match occurred for each input.
      cos_sim: (n_input, n_candidates) cosine similarity matrix between inputs and candidates
    """

    if len(features_cand)==0:
        return np.array([]), np.array([])

    assert feat_input.shape[1] == features_cand.shape[1], 'matrices should have same columns'
    assert len(cutoff_list) == len(feat_input), 'there should be one similarity cutoff for each input logo'

    cos_sim = cosine_similarity(X = feat_input, Y = features_cand)

    # similarity cutoffs are defined 3 significant digits, approximate cos_sim for consistency
    cos_sim = np.round(cos_sim, 3)

    # for each input, return matches if
    match_indices = []
    for i in range(len(feat_input)):
        # matches = [ c for c in range(len(features_cand)) if cc[i] > cutoff_list[i]]
        # alternatively in numpy, get indices of
        matches = np.where(cos_sim[i] >= cutoff_list[i])
        match_indices.append(matches)

    return match_indices, cos_sim

def draw_matches(img_test, inputs, prediction, matches):
    """
    Draw bounding boxes on image for logo candidates that match against user input.

    Args:
      img_test: input image as 3D np.array (opencv BGR ordering)
      inputs: list of annotations strings that will appear on top of each box
      prediction: logo candidates from YOLO step
      matches: array of prediction indices, prediction[matches[i]]
    Returns:
      annotated image as 3D np.array  (opencv BGR ordering)

    """

    if len(prediction)==0:
        return img_test

    image = Image.fromarray(img_test)

    colors = bbox_colors(len(inputs))
    # for internal consistency, colors in BGR notation
    colors = np.array(colors)[:,::-1]

    # for each input, look for matches and draw them on the image
    match_bbox_list_list = []
    for i in range(len(inputs)):
        match_bbox_list_list.append([])
        for match in matches[i][0]:
            match_bbox_list_list[i].append(prediction[match])

        # print('{} target: {} matches found'.format(inputs[i], len(match_bbox_list_list[i]) ))

    new_image = draw_annotated_box(image, match_bbox_list_list, inputs, colors)

    return np.array(new_image)
















def main():
    print('FILL ME')



if __name__ == '__main__':
    main()