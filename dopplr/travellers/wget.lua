wget.callbacks.download_child_p = function(urlpos, parent, depth, start_url_parsed, iri, verdict)
  if string.find(urlpos.url.url, "full_icon.png") then
    -- always download
    return true
  else
    -- follow wget's advice
    return verdict
  end
end
